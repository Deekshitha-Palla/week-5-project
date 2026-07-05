"""
test_mcp_connection.py
Isolated end-to-end test of mcp_connector.py — run this BEFORE plugging
MCP into the full agent. If this fails, the problem is your server config/
API key, not your agent code, and you'll debug it faster here.

Usage:
    python test_mcp_connection.py
"""

import asyncio
from mcp_connector import MCPManager


async def main():
    print("=" * 60)
    print("STEP 1: Connecting to configured servers")
    print("=" * 60)
    manager = MCPManager("mcp_servers.json")
    await manager.connect_all()

    if not manager.servers:
        print("\n❌ No servers connected. Check:")
        print("   - mcp_servers.json exists and has valid JSON")
        print("   - the env var named in key_env_var is set in .env")
        print("   - .env is in the same directory you're running this from")
        return

    print(f"\n✅ Connected to {len(manager.servers)} server(s)")

    print("\n" + "=" * 60)
    print("STEP 2: Listing available tools")
    print("=" * 60)
    for name, connected in manager.servers.items():
        print(f"\n[{name}]")
        for tool in connected.tools:
            print(f"  - {tool.name}: {tool.description}")

    print("\n" + "=" * 60)
    print("STEP 3: Tool schema in OpenAI format (sanity check)")
    print("=" * 60)
    tools_openai = manager.get_all_tools_openai_format()
    print(f"{len(tools_openai)} tool schema(s) ready to merge with TOOLS in agent.py")
    if tools_openai:
        import json
        print("\nFirst tool schema:")
        print(json.dumps(tools_openai[0], indent=2))

    print("\n" + "=" * 60)
    print("STEP 4: Calling a real tool")
    print("=" * 60)
    if tools_openai:
        result = await manager.call_tool(
            "resolve-library-id",
            {"query": "how to make HTTP requests", "libraryName": "requests"},
        )
        print("resolve-library-id result:")
        for chunk in result:
            print(chunk[:1500])

        print("\n" + "-" * 60)
        print("STEP 4b: Chaining query-docs with the resolved library ID")
        print("-" * 60)
        result2 = await manager.call_tool(
            "query-docs",
            {"context7CompatibleLibraryID": "/psf/requests", "query": "how to make a GET request"},
        )
        print("query-docs result:")
        for chunk in result2:
            print(chunk[:1500])
    else:
        print("No tools to call — check STEP 2 output.")

    print("\n" + "=" * 60)
    print("STEP 5: Cleanup")
    print("=" * 60)
    await manager.close_all()
    print("✅ Connections closed cleanly")


if __name__ == "__main__":
    asyncio.run(main())