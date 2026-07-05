"""
Sandboxed file tools — see week_3/2_agent_class.md

Implement:
  - resolve_path
  - read_file(path, start_line=1, read_lines=200)  — numbered lines, has_more
  - write_file(path, content)
  - edit_file(path, operation, start_line, end_line?, content?)  — replace | delete | append
  - list_files(path, pattern)
"""

# TODO: implement — see Build 2

import os
import json
import glob as glob_module

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))


def resolve_path(path: str) -> str:

    p = os.path.abspath(os.path.join(WORKSPACE_ROOT,path))
    if p.startswith(WORKSPACE_ROOT):
        return p
    else: raise ValueError("Path escapes workspace")


def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    p=resolve_path(path)
    with open(p,"r",encoding="utf-8") as f:
        lines=f.readlines()
    selected=lines[start_line-1:start_line-1+read_lines]
    content="\n".join(
        f"{i}:{line.rstrip()}" for i,line in enumerate(selected,start=start_line)
    )
    has_more = read_lines+start_line-1 < len(lines)
    return {
        "content":content,
        "has_more":has_more,
    }

def request_approval(action: str, function: str, details: dict) -> bool:
    """
    Shared approval gate — same shape as run_command's inline prompt in
    Build 1, pulled out so write_file/edit_file (and anything else) can
    reuse it instead of re-implementing the print+input() block.
    Returns True if approved, False if declined.
    """
    detail_lines = "\n            ".join(f"{k} : {v}" for k, v in details.items())
    print(f"""
        APPROVAL REQUIRED
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Action   : {action}
        Function : {function}
        {detail_lines}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    return input("Allow? [y/N]: ").strip().lower() == "y"

def write_file(path: str, content: str) -> dict:
    p=resolve_path(path)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            old_size = len(f.read())
        action = "OVERWRITE existing file — current content will be lost"
    else:
        old_size = 0
        action = "CREATE new file"
    approved = request_approval(
        action=action,
        function="write_file",
        details={
            "Path": p,
            "Current size": f"{old_size} bytes",
            "New size": f"{len(content)} bytes",
        },
    )
    if not approved:
        return {"error": "blocked: user did not approve overwrite"}
        
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(p,"w",encoding="utf-8") as f:
        write=f.write(content)
    return {
        "content": f"wrote {write} bytes"
    }


def edit_file(
    path: str,
    operation: str,
    start_line: int,
    end_line: int | None = None,
    content: str | None = None,
) -> dict:
    p=resolve_path(path)
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    end = end_line if end_line is not None else start_line
    preview = "".join(lines[start_line - 1:end]) if operation != "append" else "(new content appended at end)"
 
    approved = request_approval(
        action=f"{operation.upper()} lines {start_line}-{end if operation != 'append' else 'EOF'}",
        function="edit_file",
        details={
            "Path": p,
            "Operation": operation,
            "Affected lines (before)": preview.rstrip("\n") or "(empty)",
            "New content": content if content is not None else "(none — deletion)",
        },
    )
    if not approved:
        return {"error": "blocked: user did not approve edit"}
    if operation == "replace":
        # lines is a list — replace the slice from start_line to end_line
        # remember: list indices are 0-based, start_line is 1-based
        lines[start_line-1:end_line] = [content]
        
    elif operation == "delete":
        # delete the slice from start_line to end_line
        del lines[start_line-1:end_line]
        
    elif operation == "append":
        # add content as a new line at the end
        lines.append( "\n"+content )
    
    # Step 2: write all lines back
    with open(p, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    
    return {"content": "ok"}


def list_files(path: str = ".", pattern: str = "*") -> dict:
    full_pattern = f"{path}/{pattern}"
    recursive = "**" in pattern

    try:
        matches = glob_module.glob(full_pattern, recursive=recursive)
        matches = sorted(matches)  # consistent ordering
        return {
            "files": matches,
            "count": len(matches),
            "pattern_used": full_pattern,
            "error": None,
        }
    except Exception as e:
        return {
            "files": [],
            "count": 0,
            "pattern_used": full_pattern,
            "error": str(e),
        }
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": 
                "Read the contents of a source file."
               " Use this tool whenever you need to:"
                "- understand implementation"
                "- explain architecture"
                "- inspect classes/functions"
                "- trace execution flow"
                "- verify repository behavior"
                "Prefer read_file over guessing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to workspace root."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line to start reading from (1-based). Default 1."
                    },
                    "read_lines": {
                        "type": "integer",
                        "description": "Number of lines to read. Default 200."
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": 
                "Write content to a file, creating it (and any missing parent "
                "directories) if it doesn't exist yet. Writing a NEW file runs "
                "immediately. If the file already exists, this OVERWRITES it "
                "entirely and will pause to ask the human operator for approval "
                "first — expect that pause for existing files, it's not a failure. "
                "Use edit_file instead if you only need to change part of an "
                "existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to workspace root."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write in the file by creating the directory."
                    },
                },
                "required": ["path","content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": 
                "Modify specific lines of an EXISTING file: replace a line range, "
                "delete a line range, or append new content at the end. Every call "
                "mutates real content already in the file, so this ALWAYS pauses "
                "and shows the human operator exactly which lines are affected and "
                "what they'll become — approve before assuming the edit has happened. "
                "Use write_file instead if you're creating a new file or replacing "
                "an entire file's contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to workspace root."
                    },
                    "operation": {
                        "type": "string",
                        "description": "The mode(replace or delete or append) of operation to perform and generate a preview"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line to start editing from (1-based). Default 1."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Line where editing ends.Default None."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write in the file by creating the directory."
                    },

                },
                "required": ["path","operation","start_line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description":  "Lists filenames only."
                "Does NOT reveal implementation."
                "Use this only to discover candidate files before read_file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to workspace root."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files, e.g. '.md' or '.py'. Defaults to '*' which returns all files."
                    },
                },
            },
        },
    },
]

TOOL_REGISTRY={
    "read_file":read_file,
    "write_file":write_file,
    "edit_file":edit_file,
    "list_files":list_files,
}