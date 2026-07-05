

import json
import os
import uuid
import sys
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime, timezone
from tools.file import TOOLS as FILE_TOOLS, TOOL_REGISTRY as FILE_REGISTRY
from tools.execute import TOOLS as EXECUTE_TOOLS, TOOL_REGISTRY as EXECUTE_REGISTRY
from tools.explore import TOOLS as EXPLORE_TOOLS, TOOL_REGISTRY as EXPLORE_REGISTRY
from tools.plan import TOOLS as PLAN_TOOLS, TOOL_REGISTRY as PLAN_REGISTRY
from tools.plan import get_todos
from contextlib import AsyncExitStack



load_dotenv()

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MODEL = "gpt-4o-mini"
SESSIONS_DIR = ".agent/sessions"
AGENTS_PATHS = ("AGENTS.md", ".agent/AGENTS.md")
SUMMARY_MODEL = "meta-llama/llama-3.3-70b-instruct"
MAX_ITERATIONS=25
MAX_MESSAGES = 20
MAX_TOOL_RESULT_CHARS=1500

# BASE_PROMPT = """You are Code Scout, a coding agent working inside a real repository.

# ENVIRONMENT
# This is a Windows system. Use Windows commands only:
# - 'dir' not 'ls', 'type' not 'cat' — no 'pwd', 'tail', or 'head'
# - Backslashes for paths: tests\\certs\\valid\\ca
# - pytest runs as: python -m pytest (not just pytest)
# - The working directory is already correct — never 'cd' into it

# YOUR CAPABILITIES
# - Local tools: run_command, grep, list_definitions, list_files, file read/write, add_todos/get_todos/mark_todo
# - load_skill(name): loads a specific procedure (bug investigation, refactoring, code review, etc.) and unlocks any extra tools it needs. Call it when a request matches a listed skill's purpose, even if worded differently than its description.
# - MCP tools (when connected, e.g. Context7): live external documentation for third-party libraries — NOT for anything about this repository's own code.

# DECIDING WHERE TO LOOK — THIS IS THE PART THAT MATTERS MOST
# Before searching anything, classify the question:
# - "Does THIS repo do/use/contain X?" → repository question. Search the repo first (grep, list_definitions) — never answer from memory alone.
# - "How does LIBRARY/FRAMEWORK X behave, work, or handle Y internally?" → general/library-knowledge question. This is NOT a repository question, even if the library is used somewhere in this repo. Use load_skill or MCP docs-lookup, or answer from your own knowledge if confident. Do not grep the local repo hunting for an answer that lives in someone else's library source.
# - If genuinely unsure which type a question is, spend at most 1-2 searches checking whether the repo is actually relevant before deciding — don't exhaust every local tool before considering that the answer isn't local at all.
# Example: "Does this repo use requests?" → repo question, grep it.
# Example: "Why does a redirect strip the Authorization header in requests?" → library-knowledge question, NOT a repo question — this is asking how a third-party library behaves, not what your code does.

# INVESTIGATION DISCIPLINE
# - Identify the user's actual goal before choosing tools.
# - Use grep/list_definitions before read_file — search before reading whole files.
# - Gather only the evidence needed to support your answer — do not exhaustively search every subtopic once you have enough to answer confidently.
# - For broad questions, give a representative overview rather than exhaustive coverage.
# - Stop investigating the moment you have sufficient evidence — additional searching past that point wastes tool calls and tokens without improving the answer.

# PLANNING AND VERIFICATION
# - For multi-step tasks, call add_todos before making changes. For a single quick lookup or a one-line fix, skip it — planning overhead isn't free.
# - Run the test suite first to confirm any reported failure before proposing a fix.
# - Every file change requires human approval — explain why before proposing it.
# - Only mark a todo "completed" after running the verification command and seeing exit_code 0. Never claim a fix works without an exit code to back it up.
# - Your current session_id is {{session_id}}. Pass it to every todo tool call.

# COMMUNICATION
# - Base your final answer only on evidence you actually collected, not assumption.
# - Do not stop while an important claim remains unsupported.
# - Be concise — this system charges real tokens per turn; don't restate tool output verbatim when a summary suffices.
# """
BASE_PROMPT = """
You are Code Scout, an autonomous software engineering agent.

Your goal is to understand, modify, and debug real codebases with the discipline
of a senior software engineer.

========================
Core Principle
========================

Prefer verified evidence over assumptions.
Use hypotheses to guide investigation, but never present them as facts until verified.
ENVIRONMENT
This is a Windows system. Use Windows commands only:
- 'dir' not 'ls', 'type' not 'cat' — no 'pwd', 'tail', or 'head'
- Backslashes for paths: tests\\certs\\valid\\ca
- pytest runs as: python -m pytest (not just pytest)
- The working directory is already correct — never 'cd' into it

========================
Task Understanding
========================

DECIDING WHERE TO LOOK — THIS IS THE PART THAT MATTERS MOST
Before searching anything, classify the question:
- "Does THIS repo do/use/contain X?" → repository question. Search the repo first (grep, list_definitions) — never answer from memory alone.
- "How does LIBRARY/FRAMEWORK X behave, work, or handle Y internally?" → general/library-knowledge question. This is NOT a repository question, even if the library is used somewhere in this repo. Use load_skill or MCP docs-lookup, or answer from your own knowledge if confident. Do not grep the local repo hunting for an answer that lives in someone else's library source.
- If genuinely unsure which type a question is, spend at most 1-2 searches checking whether the repo is actually relevant before deciding — don't exhaust every local tool before considering that the answer isn't local at all.
Example: "Does this repo use requests?" → repo question, grep it.
Example: "Why does a redirect strip the Authorization header in requests?" → library-knowledge question, NOT a repo question — this is asking how a third-party library behaves, not what your code does.
Do not confuse:
- API entry points with implementations.
- File names with behavior.
- Documentation with source code.

Confidence rule for library-knowledge questions:
If you can answer from your own knowledge with reasonable confidence, DO SO — do not
ask the user "which library did you mean?" as a substitute for answering.
Only ask a clarifying question if the repo genuinely contains multiple candidate
libraries/clients AND you cannot resolve the ambiguity with 1-2 searches.
Ending a turn with "let me know if you meant X" when X was checkable is a failure,
not caution.

========================
Investigation Strategy
========================

When investigating code:

- Search before reading large files.
- Locate definitions before analyzing implementations.
- Follow data/control flow until the behavior is explained.
- If a function only forwards data, continue tracing until the data is used.
- Prefer understanding relationships between components over listing files.

Good reasoning explains:
A calls B.
B transforms C.
C produces D.

Not:
A exists.
B exists.
C exists.

Before treating a question as pure library-knowledge, spend at most 1-2 searches
confirming which library/client is actually in play, e.g.:
    grep -rn "import requests\|axios\|fetch(\|urllib3" .
This turns a vague question into a concrete one and costs less than asking the user.
Skipping this and jumping straight to a clarifying question is not allowed when a
cheap search could have resolved it.


========================
Bug Investigation
========================

For bugs or unexpected behavior:

1. Reproduce or locate the failing behavior when possible.
2. Find the responsible implementation.
3. Trace the execution path.
4. Identify the root cause.
5. Modify only the necessary code.
6. Verify with tests.

Do not give generic debugging advice when repository tools are available.

========================
Code Changes
========================

Before editing:
- Understand existing patterns.
- Make minimal targeted changes.
- Preserve existing style.
- Explain why the change is needed.

After editing:
- Run the smallest relevant verification first.
- Only claim success after observing successful results.

========================
Tool Usage
========================

Tools exist to gather evidence, not to appear active.

- Local tools: run_command, grep, list_definitions, list_files, file read/write, add_todos/get_todos/mark_todo
- load_skill(name): loads a specific procedure (bug investigation, refactoring, code review, etc.) and unlocks any extra tools it needs.Use load_skill when the task requires a reusable workflow
(debugging, implementation, review, refactoring), not for simple lookups. even if worded differently than its description.
- MCP tools (when connected, e.g. Context7): External information sources and services.Use them when they provide evidence unavailable from local repository tools.
Repository source code remains authoritative for repository behavior.
Use the cheapest reliable source:
- Search tools -> locate information.
- File reading -> understand implementation.
- Tests/commands -> verify behavior.
- If unsure, spend at most 1-2 searches checking repo-relevance before deciding —
don't exhaust every local tool before considering the answer isn't local.

For library-behavior questions specifically:
1. Confirm the library via a cheap grep (see Investigation Strategy).
2. If an MCP docs tool (e.g. Context7) is connected, use it to pull authoritative
   behavior before answering — do not rely solely on parametric memory when a
   verified source is one tool call away.
3. Only skip the MCP call if no docs-capable MCP tool is connected; in that case,
   answer from knowledge but explicitly flag it as unverified ("based on general
   knowledge, not confirmed against source docs").
"Verified evidence over assumption" applies to library behavior exactly as much as
it applies to repo behavior — external evidence is still evidence.
Avoid unnecessary tool calls.

========================
Final Answers
========================

PLANNING AND VERIFICATION
 - For multi-step tasks, call add_todos before making changes. For a single quick lookup or a one-line fix, skip it — planning overhead isn't free.
 - Reproduce the failure when possible using the smallest relevant test before modifying code.
 - Every file change requires human approval — explain why before proposing it.
 - Only mark a todo "completed" after running the verification command and seeing exit_code 0. Never claim a fix works without an exit code to back it up.
 - Your current session_id is {{session_id}}. Pass it to every todo tool call.

COMMUNICATION
 - Base your final answer only on evidence you actually collected, not assumption.
 - Do not present unsupported claims as facts.If evidence cannot be obtained, state the limitation.
 - Be concise — this system charges real tokens per turn; don't restate tool output verbatim when a summary suffices.
A good final response:
- Directly answers the user.
- References discovered evidence.
- Explains relationships and reasoning.
- Clearly separates facts from assumptions.
Never end a turn by describing what you *would* investigate when you had the tools
to investigate it this turn. A deferred plan is not a substitute for a completed
answer.

If evidence is incomplete, say what is missing.
Accuracy is more important than speed.
"""


# ----TOOL_REGISTRY
TOOLS = FILE_TOOLS + EXECUTE_TOOLS + EXPLORE_TOOLS + PLAN_TOOLS
TOOL_REGISTRY = {**FILE_REGISTRY, **EXECUTE_REGISTRY, **EXPLORE_REGISTRY, **PLAN_REGISTRY}


from skill_loader import load_skills
from skill_matcher import match_skill
from tools.paper import TOOLS as PAPER_TOOLS   # if/when you keep these separate
from tools.web import TOOLS as WEB_TOOLS
from mcp_connector import MCPManager

GATED_TOOL_GROUPS = {
     "paper": PAPER_TOOLS,
     "web": WEB_TOOLS,
}


# ---Session calls------

def create_session() -> str:
    """Return a new 8-char hex session ID."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    # TODO: initiate a new, empty session with a unique ID
    session_id=uuid.uuid4().hex[:8]
    session={
        "session_id":session_id,
        "createdAt":datetime.now().isoformat(),
        "updatedAt":datetime.now().isoformat(),
        "status":"initialised",
        "title":"Untitled",
        "metadata":{
            "cwd":"",
            "version":"",
        },
        "history":[],
    }
    path=f".agent/sessions/{session_id}.json"
    with open(path, "w", encoding="utf-8") as f: 
        json.dump(session, f, indent=2)
    return session_id


def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    path = f".agent/sessions/{session_id}.json"
    clean_messages = [m if isinstance(m, dict) else m.model_dump() for m in messages]

    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing.update({
        "session_id": session_id,
        "title": title,
        "history": clean_messages,
        "updatedAt": datetime.now().isoformat(),
        "status": "finished",
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
        


def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    # TODO: implement
    path=f".agent/sessions/{session_id}.json"
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            return json.loads(f.read())
    else: return {"messages": []}


def list_sessions() -> list[dict]:
    """Return sessions sorted by updated_at descending."""
    # TODO: implement
    sessions = [] 
    for filename in os.listdir(SESSIONS_DIR): 
        if filename.endswith(".json"): 
            path = os.path.join(SESSIONS_DIR, filename) 
            with open(path, "r", encoding="utf-8") as f: 
                sessions.append(json.load(f)) 
    sessions.sort( key=lambda session: session["updatedAt"], reverse=True ) 
    return sessions

# -------------Agent loop----------------------------------------

class Agent:
    """Core agent: loop, tools, sessions. No UI."""

    def __init__(self, workspace: str = ".", session_id: str | None = None):
        self.workspace = os.path.abspath(workspace)
        # TODO: session_id, load messages
        if session_id is not None:
            self.session_id=session_id
            session=load_session(session_id)
            self.messages=session["history"]
            self.title = session.get("title", "Untitled")
        else:
            self.session_id=create_session()
            self.messages = [{"role": "system", "content": build_system_prompt().replace("{{session_id}}", self.session_id)}]
            self.title = "Untitled"
        self.mcp = MCPManager("mcp_servers.json")
        self.skills = load_skills("skills")
        pass
    
    async def async_init(self):
        await self.mcp.connect_all()

    async def chat(self, user_message: str) -> str:
        # TODO: append user msg, _run_loop(), save session, return answer
        self.messages.append({"role": "user", "content": user_message})
        matched = match_skill(user_message, self.skills)
        gated_tools, skill_note = [], None
        if matched:
            for group in matched.gated_groups:
                gated_tools += self.mcp.get_all_tools_openai_format() if group == "mcp" \
                    else GATED_TOOL_GROUPS.get(group, [])
            skill_note = {"role": "system", "content": f"[Active skill: {matched.name}]\n{matched.body}"}
            self._emit("skill_matched", name=matched.name)

        self._all_tools = TOOLS + [self._build_load_skill_tool()] + gated_tools
        self._skill_note = skill_note
        answer=await self._run_loop()
        if self.title == "Untitled":
            self.title = user_message[:50] + ("..." if len(user_message) > 50 else "")
        save_session(self.session_id,self.messages,title=self.title)
        return answer
    
    # In Agent class, add these two methods:

    def _build_load_skill_tool(self) -> dict:
        listing = "\n".join(f"- {s.name}: {s.description}" for s in self.skills)
        return {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": (
                    "Load a skill's full procedure and unlock any tools it requires, "
                    "when the user's request matches a skill's purpose even if worded "
                    "differently than its description below. Available skills:\n" + listing
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string", "description": "Exact name of the skill to load, e.g. 'bug_investigation'."}
                    },
                    "required": ["skill_name"],
                },
            },
        }

    def _load_skill(self, skill_name: str) -> dict:
        match = next((s for s in self.skills if s.name == skill_name), None)
        if not match:
            return {"error": f"no skill named '{skill_name}'", "available_skills": [s.name for s in self.skills]}
        added = []
        for group in match.gated_groups:
            extra = self.mcp.get_all_tools_openai_format() if group == "mcp" else GATED_TOOL_GROUPS.get(group, [])
            existing_names = {t["function"]["name"] for t in self._all_tools}
            for t in extra:
                if t["function"]["name"] not in existing_names:
                    self._all_tools.append(t)
                    added.append(t["function"]["name"])
        return {"skill": match.name, "instructions": match.body, "newly_unlocked_tools": added}
    
    async def run_once(self, prompt: str) -> str:
        return await self.chat(prompt)
    
    async def _run_tool_call(self, tool):
        self._emit("tool_call", name=tool.function.name)
        reply = await self.dispatch(tool)
        if len(reply) > MAX_TOOL_RESULT_CHARS:
            reply = reply[:MAX_TOOL_RESULT_CHARS] + "\n\n[...truncated]"
        return {"role": "tool", "tool_call_id": tool.id, "content": reply}

    async def _compact_old_messages(self) -> None:
        if len(self.messages) <= MAX_MESSAGES:
            return
        system = self.messages[0]
        keep_recent = MAX_MESSAGES - 2
        old = self.messages[1:-keep_recent]
        recent = self.messages[-keep_recent:]
        if not old:
            return
        
        # advance past any orphaned tool messages at the start of recent
        while recent and (recent[0] if isinstance(recent[0], dict) else recent[0].model_dump()).get("role") == "tool":
            recent = recent[1:]
        
        try:
            old_text = "\n".join(f"{m.get('role','?')}: {str(m.get('content',''))[:300]}" for m in old if isinstance(m, dict))
            resp =await client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=[{"role": "user", "content": f"Summarize this conversation in 2-3 sentences:\n\n{old_text}"}],
                max_tokens=150,
            )
            summary = resp.choices[0].message.content or "Earlier conversation occurred."
        except Exception:
            summary = "Earlier conversation occurred (summary unavailable)."
        
        compacted = {"role": "system", "content": f"[Earlier context summary]: {summary}"}
        self.messages = [system, compacted] + recent

    async def _run_loop(self) -> str:
        # TODO: agent loop — call self.dispatch(), self._emit() on tool calls
        for i in range(MAX_ITERATIONS):
            await self._compact_old_messages()
            api_messages = self.messages
            if self._skill_note:
                api_messages = self.messages[:1] + [self._skill_note] + self.messages[1:]
            response=await client.chat.completions.create(
                model=MODEL,
                messages=api_messages,
                temperature=0.3,
                top_p=0.9,
                tools=self._all_tools,
                max_tokens=512,
            )
            message=response.choices[0].message
            self.messages.append(message)
            if not message.tool_calls:
                todos = get_todos(self.session_id)
                pending = todos.get("counts", {}).get("pending", 0) + todos.get("counts", {}).get("in_progress", 0)
                if pending > 0:
                    self.messages.append({
                        "role":"system",
                        "content":"There are pending todos.Either continue working OR explain why they cannot be completed."
                    })
                    continue
                return message.content or ""

            # in _run_loop, replace the for-loop with:
            if message.tool_calls:
                results = await asyncio.gather(*(self._run_tool_call(t) for t in message.tool_calls))
                self.messages.extend(results)
                continue
        return "Hit iteration limit."
        

   # In dispatch(), route it before the existing checks, restore try/except:
    async def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
            if name == "load_skill":
                return json.dumps(self._load_skill(args.get("skill_name", "")))
            if name in TOOL_REGISTRY:
                return json.dumps(TOOL_REGISTRY[name](**args))
            elif name in self.mcp.tool_to_server:
                result = await self.mcp.call_tool(name, args)
                return json.dumps(result)
            return f"Unknown tool:{name}"
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _trim_messages(self) -> None:
        if len(self.messages) > MAX_MESSAGES:
            system = self.messages[0]
            recent = self.messages[-(MAX_MESSAGES - 1):]
            self.messages = [system] + recent

    def _emit(self, event: str, **data) -> None:
        """Override in REPLAgent/TUIAgent for tool logging."""
        pass

class REPLAgent(Agent):
    async def run(self) -> None:
        print(f"Research Desk [{self.session_id}] — /quit to exit, /sessions to list, /resume <id> to switch")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                await self.mcp.close_all()
                break

            if not user_input or user_input in ("/quit", "/exit"):
                await self.mcp.close_all()
                break

            if user_input == "/sessions":
                sessions = list_sessions()
                for s in sessions:
                    marker = "→" if s["session_id"] == self.session_id else " "
                    print(f"{marker} {s['session_id']}  |  {s.get('title', 'Untitled')}  |  {s['updatedAt']}")
                print()
                continue

            if user_input.startswith("/resume "):
                new_id = user_input.split(" ", 1)[1].strip()
                session = load_session(new_id)
                if session.get("messages") == [] and not os.path.exists(f"{SESSIONS_DIR}/{new_id}.json"):
                    print(f"Session {new_id} not found.")
                    continue
                self.session_id = new_id
                self.messages = session["history"]
                print(f"Resumed session [{new_id}]")
                continue
            if user_input == "/skills":
                for s in self.skills:
                    print(f"  {s.name:25} {s.description[:80]}")
                print()
                continue

            if user_input.startswith("/mcp"):
                parts = user_input.split()
                if len(parts) == 2 and parts[1] == "list":
                    for s in self.mcp.status():
                        marker = "✅" if s["connected"] else "⬜"
                        print(f"  {marker} {s['name']:20} {s['tool_count']} tools")
                elif len(parts) == 3 and parts[1] == "enable":
                    await self.mcp.enable(parts[2])
                elif len(parts) == 3 and parts[1] == "disable":
                    await self.mcp.disable(parts[2])
                else:
                    print("  usage: /mcp list | /mcp enable <name> | /mcp disable <name>")
                print()
                continue

            print(await self.chat(user_input))
            print()

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [tool] {data.get('name')}", file=sys.stderr)

def build_system_prompt() -> str:
    final_prompt=BASE_PROMPT
    for p in AGENTS_PATHS:
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f:
                final_prompt+=f.read()
    return final_prompt


async def main():
    args = sys.argv[1:]
    session_id = None
    
    if "--session" in args:
        idx = args.index("--session")
        session_id = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    
    # if "--tui" in args:
    #     args.remove("--tui")
    #     from tui import TUIAgent
    #     agent = TUIAgent(session_id=session_id)                   
    #     agent.run()
    #     return
    
    agent = REPLAgent(session_id=session_id)
    await agent.async_init()
    if args:
        print(await agent.run_once(" ".join(args)))
        print(f"\n[session: {agent.session_id}]", file=sys.stderr)
        await agent.mcp.close_all()
        return
    await agent.run()                        

if __name__ == "__main__":
    asyncio.run(main())
    
