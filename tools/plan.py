"""
Build 3: Todo Tools
======================
A todo list the model maintains itself — what it's planning to do, what
it's actually done, and how it'll know each item really worked.

This build is intentionally less prescriptive than Builds 1 and 2. You
decide the exact shape of a todo and how the list is stored — in memory,
in a dict, in a JSON file under .agent/, however you like. The one hard
requirement, from Lesson 2: every todo needs a short title, a
description, and a verification method — some concrete, checkable way
to know the item is actually done ("run pytest tests/test_auth.py and
confirm exit code 0"), not just a status flag the model sets on its own
say-so.

Tasks (design these yourself — the signatures below are a starting
point, not a contract you have to match):
  1. add_todos(...)  — add one or more todos to the list
  2. get_todos(...)  — return the current list, however you choose to
     filter or shape it
  3. mark_todo(...)  — update a todo's status
  4. Once you've settled on a shape, write the TOOLS schema yourself
     and wire it into the agent loop's stop condition (Lesson 2) — the
     loop shouldn't consider itself done while a todo is incomplete.

Questions to resolve before you write code — there's no single right
answer, but you should be able to defend whatever you pick:
  - What does "status" need to express? pending/in_progress/completed
    is Lesson 2's minimum — is that enough once verification enters
    the picture, or do you need something like "blocked" too?
  - Should mark_todo require evidence (e.g. a command's exit code)
    before it'll accept "completed," and refuse otherwise? Lesson 2's
    "Completed Should Mean Verified, Not Just Claimed" argues yes —
    decide how strict to make that in code.
  - Where does the list live, and what survives a resumed session
    (Week 3)? A module-level list won't survive a process restart;
    is that good enough for this build, or do you need it on disk?
  - Should add_todos take one todo or a whole plan at once? (Lesson 2's
    todo_write always sends the full current list back — you don't
    have to copy that design, but know why it might matter.)

Run directly once you've implemented something real: add a couple of
todos, mark one in_progress, try to mark it completed without evidence
and see whether your own rules let that happen, then get_todos() and
confirm the list reflects what you'd expect.
"""
import json
import os
import uuid

# TODO: pick your own storage. A plain list/dict at module scope is fine
# to start; revisit once you decide whether todos need to survive a
# resumed session.


TODO_FILE = ".agent"

def _todo_file(session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    return os.path.join(TODO_FILE, f"todos_{session_id}.json")

def _session_exists(session_id: str) -> bool:
    return os.path.exists(_todo_file(session_id))
 
def _load(session_id: str) -> list:
    path = _todo_file(session_id)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)
 
 
def _save(session_id: str, todos: list) -> None:
    path = _todo_file(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(todos, f, indent=2)                                                         # if storing all tasks into a directory run out of storage at some point of time,then what to do?

# implement the following: add_todos, get_todos, mark_todo
def add_todos(session_id: str,items:list[dict]) -> dict:
    new= _load(session_id)
    N=0
    for i in items:
        task_id=uuid.uuid4().hex[:8]
        new.append({
            "id":task_id,
            "title":i.get("title",""),
            "description":i.get("description",""),
            "status":"pending",
            "verification":i.get("verification",""),
            "evidence":"",
        })
        N=N+1
    _save(session_id, new)
    return {"added":N}
    
def get_todos(session_id: str,status: str = None) -> dict:
    if not _session_exists(session_id):
        return {"error": f"no plan found for session {session_id}"}
    todos = _load(session_id)
    if status:
        filtered = [t for t in todos if t["status"] == status]
    else:
        filtered = todos
    return {
        "todos": filtered,
        "counts": {
            "pending":    len([t for t in todos if t["status"] == "pending"]),
            "in_progress": len([t for t in todos if t["status"] == "in_progress"]),
            "completed":  len([t for t in todos if t["status"] == "completed"]),
            "failed":     len([t for t in todos if t["status"] == "failed"]),
        },
    }
            
    
def mark_todo(session_id: str,task_id: str, status: str, evidence: str = "") -> dict:
    if not _session_exists(session_id):
        return {"error": f"no plan found for session {session_id}"}
    task=_load(session_id)
    for t in task:
        if t["id"]==task_id:
            if status=="completed" and evidence=="":
                return {"error": "evidence required to mark completed"}
            else:
                t["status"]=status
                t["evidence"]=evidence
                _save(session_id,task)
                return {"ok": True}
    return {"error": f"todo {task_id} not found"}
    

# TODO: once the functions above have a settled shape, write the TOOLS
# schema for add_todos / get_todos / mark_todo yourself. Lesson 6 has
# the guidance on what makes a tool description the model actually
# follows — apply it here instead of copying Lesson 2's example verbatim.
TOOLS = [
    {
        "type":"function",
        "function":{
            "name":"add_todos",
            "description":"Create a plan by adding one or more todo items to the task list. "
                          "Call this early, after you understand the scope of work, before making any changes. "
                          "Each item needs a title, description, and a concrete verification command.",
            "parameters": {
                "type": "object",
                    "properties":{
                        "session_id": {
                                "type": "string",
                                "description": "The current session's id. Always pass the session_id you were given.",
                        },
                        "items": {
                            "type": "array",
                            "description": "List of todo items to add.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Short task title."},
                                    "description": {"type": "string", "description": "What needs to be done."},
                                    "verification": {"type": "string", "description": "Command to run to verify completion, e.g. 'pytest tests/test_auth.py'."},
                                },
                                "required": ["title", "description", "verification"],
                            },
                        },
                },
                "required": ["session_id","items"],
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"get_todos",
            "description":"Get the current todo list with status counts. "
                          "Use this to check progress, decide what to work on next, "
                          "or confirm all tasks are complete before finishing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "The current session's id. Always pass the session_id you were given.",
                    },
                    "status":{
                        "type":"string",
                        "enum": ["pending", "in_progress", "completed", "failed"],
                        "description":"Optional filter — return only todos with this status. Omit to get the full list.",
                    },
                }, 
                "required": ["session_id"],   
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"mark_todo",
            "description":"Update a todo item's status. To mark something completed, "
                          "you MUST provide evidence — the actual output or exit code from "
                          "running the verification command. Claiming completion without "
                          "evidence will be rejected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "The current session's id. Always pass the session_id you were given.",
                    },
                    "task_id":{
                        "type":"string",
                        "description":"The particular task id to check the perfect evidence of completion"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "failed"],
                        "description": "New status of the task."
                    },
                    "evidence":{
                        "type":"string",
                        "description":"Required when status is 'completed' — output or exit code proving the verification command succeeded.",
                    },
                },
            "required":["session_id","task_id","status","evidence"],    
            },
        },
    },
]

TOOL_REGISTRY={
    "add_todos":add_todos,
    "get_todos":get_todos,
    "mark_todo":mark_todo,
}

# if __name__ == "__main__":
#     # TODO: exercise add_todos / get_todos / mark_todo once they're real,
#     # including the case where you try to mark something completed
#     # without evidence — does your code stop you, or let it through?
#     # print(add_todos([
#     #     {"title": "Fix auth bug", "description": "Token validation failing", "verification": "pytest tests/test_auth.py"},
#     #     {"title": "Update docs", "description": "README outdated", "verification": "cat README.md"},
#     # ]))

#     # # get all todos
#     # print(get_todos())

#     # # try marking complete WITHOUT evidence — should fail
#     # todos = get_todos()["todos"]
#     # first_id = todos[0]["id"]
#     # print(mark_todo(first_id, "completed", evidence=""))

#     # # mark complete WITH evidence — should work
#     # print(mark_todo(first_id, "completed", evidence="exit code 0, all tests passed"))

#     # # confirm state
#     # print(get_todos())
#     sid = "demo-session"
 
#     print(add_todos(sid, [
#         {"title": "Fix auth bug", "description": "Token validation failing", "verification": "pytest tests/test_auth.py"},
#         {"title": "Update docs", "description": "README outdated", "verification": "cat README.md"},
#     ]))
 
#     print(get_todos(sid))
 
#     todos = get_todos(sid)["todos"]
#     first_id = todos[0]["id"]
 
#     # try marking complete WITHOUT evidence — should fail
#     print(mark_todo(sid, first_id, "completed", evidence=""))
 
#     # mark complete WITH evidence — should work
#     print(mark_todo(sid, first_id, "completed", evidence="exit code 0, all tests passed"))
 
#     print(get_todos(sid))
#     pass
