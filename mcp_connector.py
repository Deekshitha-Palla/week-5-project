"""
mcp_connector.py
Multi-server MCP client for Code Scout.

Connects to one or more remote MCP servers over Streamable HTTP,
authenticating via an API key passed as a header (no OAuth flow).
Sessions are opened once and kept alive for the life of the agent run,
with automatic reconnect if a call fails.

Server config lives in mcp_servers.json (name, url, key_env_var).
Actual secrets live in .env — never in the JSON.

Usage:
    manager = MCPManager("mcp_servers.json")
    await manager.connect_all()
    tools = manager.get_all_tools_openai_format()   # merge into your LLM tool list
    result = await manager.call_tool("context7_get_docs", {"library": "requests"})
    await manager.close_all()
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


@dataclass
class ServerConfig:
    name: str
    url: str
    key_env_var: str
    header_name: str = "Authorization"
    header_format: str = "Bearer {key}"  # some servers want raw key, not "Bearer x"


@dataclass
class ConnectedServer:
    config: ServerConfig
    session: ClientSession
    tools: list = field(default_factory=list)


class MCPManager:
    def __init__(self, config_path: str = "mcp_servers.json"):
        self.config_path = config_path
        self.configs: dict[str, ServerConfig] = {c.name: c for c in self._load_configs()}
        self.servers: dict[str, ConnectedServer] = {}
        self.tool_to_server: dict[str, str] = {}
        # one AsyncExitStack PER server (not shared) — lets us close a single
        # server via disable() without tearing down every other connection
        self._stacks: dict[str, AsyncExitStack] = {}

    def _load_configs(self) -> list[ServerConfig]:
        with open(self.config_path) as f:
            raw = json.load(f)
        return [ServerConfig(**entry) for entry in raw["servers"]]

    async def connect_all(self):
        """Connect to every configured server. Skips (warns, doesn't crash)
        any server whose key is missing or that fails to connect, so one
        bad server doesn't take down the whole agent."""
        for cfg in self.configs.values():
            try:
                await self._connect_one(cfg)
            except Exception as e:
                print(f"[mcp] WARN: could not connect to '{cfg.name}': {e}")

    async def enable(self, name: str) -> bool:
        """Connect a single server by name. Returns True on success."""
        cfg = self.configs.get(name)
        if cfg is None:
            print(f"[mcp] no server named '{name}' in {self.config_path}")
            return False
        if name in self.servers:
            print(f"[mcp] '{name}' already connected")
            return True
        try:
            await self._connect_one(cfg)
            return True
        except Exception as e:
            print(f"[mcp] WARN: could not connect to '{name}': {e}")
            return False

    async def disable(self, name: str) -> bool:
        """Close one server's session and drop its tools, leaving others untouched."""
        if name not in self.servers:
            print(f"[mcp] '{name}' isn't connected")
            return False
        await self._stacks[name].aclose()
        del self._stacks[name]
        del self.servers[name]
        self.tool_to_server = {t: s for t, s in self.tool_to_server.items() if s != name}
        print(f"[mcp] disconnected '{name}'")
        return True

    def status(self) -> list[dict]:
        """For /mcp list — every known server and whether it's currently connected."""
        return [
            {"name": name, "connected": name in self.servers,
             "tool_count": len(self.servers[name].tools) if name in self.servers else 0}
            for name in self.configs
        ]

    async def _connect_one(self, cfg: ServerConfig):
        api_key = os.environ.get(cfg.key_env_var)
        if not api_key:
            raise ValueError(f"env var '{cfg.key_env_var}' not set")

        header_value = cfg.header_format.format(key=api_key)
        headers = {cfg.header_name: header_value}

        stack = AsyncExitStack()
        read, write, _ = await stack.enter_async_context(
            streamablehttp_client(cfg.url, headers=headers)
        )
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        tools_result = await session.list_tools()
        connected = ConnectedServer(config=cfg, session=session, tools=tools_result.tools)
        self.servers[cfg.name] = connected
        self._stacks[cfg.name] = stack

        for tool in tools_result.tools:
            self.tool_to_server[tool.name] = cfg.name

        print(f"[mcp] connected to '{cfg.name}' ({len(tools_result.tools)} tools)")

    async def call_tool(self, tool_name: str, arguments: dict, retries: int = 1):
        """Call a tool by name, routing to whichever server owns it.
        On failure, tries one reconnect before giving up.
        Returns a JSON-serializable value (list of strings), matching what
        Agent.dispatch() expects to json.dumps() before appending as a
        'tool' message."""
        server_name = self.tool_to_server.get(tool_name)
        if server_name is None:
            raise KeyError(f"no connected MCP server exposes tool '{tool_name}'")

        connected = self.servers[server_name]
        try:
            result = await connected.session.call_tool(tool_name, arguments)
            # result.content is a list of TextContent/ImageContent objects —
            # flatten to plain text so it's directly json.dumps-able
            return [
                c.text if hasattr(c, "text") else str(c)
                for c in result.content
            ]
        except Exception as e:
            if retries <= 0:
                raise
            print(f"[mcp] call to '{tool_name}' failed ({e}), reconnecting '{server_name}'...")
            if server_name in self._stacks:
                await self._stacks[server_name].aclose()
            await self._connect_one(connected.config)
            return await self.call_tool(tool_name, arguments, retries=retries - 1)

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Used in Agent.dispatch() to route: local TOOL_REGISTRY vs MCP."""
        return tool_name in self.tool_to_server

    def get_all_tools_openai_format(self) -> list[dict]:
        """Flatten every connected server's tools into OpenAI/OpenRouter-style
        function-calling schemas, ready to merge with your local tool list."""
        merged = []
        for connected in self.servers.values():
            for tool in connected.tools:
                merged.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                })
        return merged

    async def close_all(self):
        for stack in list(self._stacks.values()):
            await stack.aclose()
        self._stacks.clear()
        self.servers.clear()
        self.tool_to_server.clear()


# ---------------------------------------------------------------------------
# Example config file to place alongside this module (mcp_servers.json):
#
# {
#   "servers": [
#     {
#       "name": "context7",
#       "url": "https://mcp.context7.com/mcp",
#       "key_env_var": "CONTEXT7_API_KEY",
#       "header_name": "Authorization",
#       "header_format": "Bearer {key}"
#     }
#   ]
# }
#
# And in .env:
#   CONTEXT7_API_KEY=your_key_here
# ---------------------------------------------------------------------------


async def _demo():
    manager = MCPManager("mcp_servers.json")
    await manager.connect_all()
    print(json.dumps(manager.get_all_tools_openai_format(), indent=2)[:1000])
    await manager.close_all()


if __name__ == "__main__":
    asyncio.run(_demo())