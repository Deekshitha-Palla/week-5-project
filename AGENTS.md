# Code Scout Rules

## Investigation Policy

Before answering repository questions:
1. Decide what information is needed.
2. Choose the appropriate tools.
3. Gather enough evidence to support important claims.
4. If evidence is insufficient, continue investigating.
5. Do not guess when the repository can verify the answer.

## Evidence
- Directory listings describe repository structure.
- Source files describe implementation and behavior.
- Architectural or behavioral claims should be supported by inspected code.
- Prefer evidence over assumptions.

## Tool Strategy

Use tools according to the information needed.
- list_files → discover repository structure
- grep → locate implementations, symbols, and usages
- list_definitions → inspect file outline
- read_file → inspect implementation
- run_command → run tests, git commands, and other shell commands

## Planning
- For any task with more than one sub-question, call todo_write first with
  your full plan before doing anything else
- Update todo_write as items complete — don't batch updates to the end
- A todo item that changes code is not "completed" until the relevant
  verification command (usually the test suite) has actually exited 0 —
  cite the exit code as evidence

## Citations
- Always cite file:line for any claim about behavior
- If grep/run_command returns zero results, try a broader term before
  reporting that something doesn't exist
  
## Environment
- Windows machine, PowerShell terminal
- Target repo is at: target_repo/
- Run commands from project root, NOT from inside target_repo/
- Use `python -m pytest target_repo/tests/...` not `cd target_repo && pytest`

## Exploration Priority
Before reading arbitrary files via grep results, first read the package's
__init__.py (or main entry point) to identify which internal modules are
exported/central versus peripheral. Prioritize central modules. Don't let
grep matches alone determine what's architecturally important — a class
appearing in many search results isn't necessarily more central than one
that's simply exported in __init__.py.
- Repository-first policy:
If the answer may depend on the current repository, verify it using repository evidence before answering. Otherwise, answer from general knowledge.

## Tool usage order
1. **Identify Entry Points**: Use tools like `list_definitions` to find where execution starts in the codebase.
2. **Gather Major Components**: Use `grep` to identify key classes and functions, along with their responsibilities.
3. **Trace Dependencies**: Analyze how components interact and depend on each other.
4. **Trace Control Flow**: Follow a representative path through the code to understand how it operates.
5. **Summarize Findings**: Provide a clear and concise summary based on the gathered evidence.

1. run_command to confirm failure first
2. add_todos immediately after first diagnostic
3. grep/list_definitions before read_file
4. write_file/edit_file for code changes (require approval)
5. run_command to verify fix

## Windows commands to use
- List files: `dir target_repo\tests\certs\valid`
- Delete file: `del target_repo\tests\certs\valid\ca`  
- Create dir: `mkdir target_repo\tests\certs\valid\ca`
- Copy file: `copy target_repo\tests\certs\expired\ca\ca.crt target_repo\tests\certs\valid\ca\ca.crt`
- Read file: `type target_repo\tests\certs\valid\ca`

## Verification rule
Never mark a todo complete without exit_code 0 from pytest.

## Never write:
- Avoid uncertain language ("likely", "appears", "seems", "probably") when the repository can verify the claim.
Inspect first.

## Tracing Execution Flow
When asked to explain how something works or what an architecture is,
do not just list files and summarize each one. Instead, trace the actual
call chain starting from the public entry point:
1. Find the entry point (often api.py, __init__.py, or the function the
   user would actually call, e.g. requests.get())
2. Read that function's implementation — what does it call next?
3. grep for the definition of whatever it calls, read that
4. Repeat: each step should answer "what happens after this line runs?"
5. Stop when you reach an external dependency (e.g. urllib3) or the
   original question is answered
6. Present the answer as a numbered sequence of steps, each citing
   file:line, e.g.:
     1. requests.get() in api.py:73 calls Session.request()
     2. Session.request() in sessions.py:XXX builds a PreparedRequest
     This is different from listing files — it's following one path through
the code, the way a developer would step through a debugger.
If a value is only passed through a function, continue tracing until you reach the function that actually uses or transforms it.

## Before producing a final answer:
When tracing execution, continue following project function calls until:
- the implementation reaches an external dependency,
- the requested behavior has been explained, or
- additional investigation is unlikely to change the answer.
For each important claim:
- Whether you have observed evidence for the answer?
- Which tool result supports it?
- If none, inspect more.

## Stopping Condition
- Do not stop investigating simply because you have found one relevant file.
- Stop when the collected evidence is sufficient to answer the user's question.

## Papers (required tools)
- Use `paper_search` for ML research and literature questions
- Use `read_paper` with the arxiv_id from search results — do not guess IDs
- If `read_paper` returns 404, fall back to `web_fetch` on arxiv.org/abs/...
- Do not use web_search when paper_search is the right tool

## Web search
- Use `web_search` before `web_fetch` for non-paper questions
- Do not fetch more than 3 pages per question unless the user asks for depth