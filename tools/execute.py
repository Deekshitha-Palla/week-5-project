"""
Build 1: Command Execution
============================
A sandboxed run_command tool: search, inspect history, run tests — and,
once a human approves, make real changes to the repo.

Tasks:
  1. paths_within_sandbox(command, workspace_root) -> bool
  2. classify_command(command) -> "read_only" | "ask"
  3. run_command(command, cwd=WORKSPACE_ROOT, timeout=10) -> dict
  4. Wire run_command into the OpenAI tool schema (TOOLS)

Run directly: a read-only command should run immediately; a destructive
one should print a warning and wait for y/n before doing anything.
"""

import os
import shlex
import subprocess

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))

WORKSPACE_ROOT = os.path.abspath(
    os.environ.get("WORKSPACE_ROOT", PROJECT_ROOT)
)

TARGET_REPO = os.path.abspath(
    os.environ.get(
        "TARGET_REPO",
        os.path.join(WORKSPACE_ROOT, "target_repo"),
    )
)
TIMEOUT_DEFAULT = 10
MAX_OUTPUT_CHARS = 8_000

# Known-safe: run immediately once the path check passes.
READ_ONLY_PREFIXES = (
    "grep", "find", "ls", "cat", "head", "tail", "wc",
    "git log", "git diff", "git status", "git blame", "git show",
    "pytest", "python -m pytest", "ruff", "flake8", "mypy", "dir", "type", "where", "echo","powershell -Command \"Get-ChildItem",
"powershell -Command \"Get-Item", "pwd", "cd", "powershell", "python -c", "python -m",
)

# Known-destructive: always ask, even if they'd otherwise look harmless.
DESTRUCTIVE_PATTERNS = (
    "rm ", "mv ", ">", ">>", "git commit", "git push", "git checkout --",
    "pip install", "npm install", "curl ", "sudo ", "chmod ",
)
COMMAND_EXPLANATIONS = {
    "rm ": "DELETE files or directories permanently — cannot be undone",
    "mv ": "MOVE or RENAME files — destination will be overwritten if it exists",
    "git commit": "COMMIT staged changes to git history",
    "git push": "PUSH local commits to remote repository",
    "pip install": "INSTALL a Python package into your environment",
    "npm install": "INSTALL Node.js packages into your environment",
    "chmod ": "CHANGE file permissions",
    "sudo ": "RUN command as root — has full system access",
    "curl ": "MAKE a network request — could download and execute code if piped to sh",
    ">": "OVERWRITE a file with command output",
    ">>": "APPEND command output to a file",
}


def paths_within_sandbox(command: str, workspace_root: str) -> bool:
    # print("Command:", command)
    # print("Workspace:", workspace_root)

    try:
        tokens = shlex.split(command,posix=False)
    except ValueError:
        return False

    print("Tokens:", tokens)

    for token in tokens:
        if token.startswith("-"):
            continue

        candidate = os.path.abspath(os.path.join(workspace_root, token))

        if os.path.exists(candidate):
            if not candidate.startswith(workspace_root):
                return False

    return True

SAFE_REDIRECTS = ("2>nul", "2>&1", "2>/dev/null")

def classify_command(command: str) -> str:
    """
    Return "read_only" if `command` matches a known-safe prefix and no
    destructive pattern, otherwise "ask".

    Default to "ask" for anything unclassified — see Lesson 1.
    """
    # TODO: implement
    # _ = command
    # wow moment
    if any(pattern in command for pattern in DESTRUCTIVE_PATTERNS):
        return "ask"

    if any(command.startswith(prefix) for prefix in READ_ONLY_PREFIXES):
        return "read_only"

    return "ask"
   
def explain_command(command: str) -> str:
    for pattern, explanation in COMMAND_EXPLANATIONS.items():
        if pattern in command:
            return explanation
    return "Unclassified command — purpose unknown, review carefully"
       
def run_command(command: str, cwd: str = PROJECT_ROOT, timeout: int = TIMEOUT_DEFAULT) -> dict:
    """
    Run a shell command, sandboxed to `cwd`.

    Behavior:
      - reject immediately if paths_within_sandbox() fails
      - if classify_command() == "read_only": execute right away
      - otherwise: print the command + a clear warning, input() for y/n,
        and block (return {"error": ...}) if the human declines
      - always: capture stdout/stderr/exit_code, truncate long output,
        and enforce `timeout`
    """
    # TODO: implement using subprocess.run(..., shell=True, cwd=cwd,
    # timeout=timeout, capture_output=True, text=True)
    # _ = (command, cwd, timeout)
    if not paths_within_sandbox(command,cwd):
        return {"error": "blocked: path outside sandbox"}
    if classify_command(command)!="read_only":
        print(f"""
            APPROVAL REQUIRED
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Command : {command}
            Function : {explain_command(command)}
            Working : {cwd}
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """)
        if input("Allow? [y/N]: ").strip().lower() != "y":
            return {"error": "blocked: user did not approve"}
        
    try:
        
        result=subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            text=True,
            timeout=timeout,
            capture_output=True,
            )
        return {
            "stdout":result.stdout[:MAX_OUTPUT_CHARS],
            "stderr": result.stderr[:MAX_OUTPUT_CHARS],
            "exit_code":result.returncode,
            "truncated": (
                len(result.stdout) > MAX_OUTPUT_CHARS
                or len(result.stderr) > MAX_OUTPUT_CHARS
            ),
        }
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": 
                "Run a shell command in the workspace and return its output. "
                "Use this to search (grep/find), inspect history (git log/diff), "
                "run tests, or make a change. Read-only commands run immediately. "
                "Anything that writes, deletes, or installs will pause and ask the "
                "human operator for approval — expect that pause, it's not a failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": f"Seconds before the command is killed. Default {TIMEOUT_DEFAULT}.",
                    },
                },
                "required": ["command"],
            },
        },
    }
]

TOOL_REGISTRY={
    "run_command":run_command,
}


# if __name__ == "__main__":
#     # print("Read-only command (should run immediately):")
#     # print(run_command("git log --oneline -5"))

#     # print("\nDestructive command (should pause and ask for approval):")
#     print(run_command("echo hello > temp.txt"))
#     print(run_command("move temp.txt temp2.txt"))



