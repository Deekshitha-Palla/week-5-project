---------
name: bug investigation
description: Whenever the user asks to "resolve the error/test failure" or "why is it failing" or "find the bug" or "what is the problem /broken behavior of the codebase" or anything to fix any error though no mention about the word "bug" explicitly
---------

# Bug investigation

## Trigger conditions
When the user asks "this is broken," "getting an error," "test is failing", "not working as expected" or" for fix the bug" then use this skill 

## Tools required
Core(always loaded): run_command, grep, list_definitions,file tools, add_todos/grt-todos/mark_todo
Gated (load only if needed): docs-lookup (MCP/Context7) — only if the bug involves a third-party library's documented behavior

## Workflow
1. **Reproduce first.** Run the failing test/command via run_command before touching any code. Never diagnose from the bug report alone — evidence over assumption.
2. **Isolate.** Use grep + list_definitions to trace from the error/stack trace to the relevant function(s). Don't read whole files blind.
3. **Plan.** add_todos with the fix + a concrete verification command (the same one that reproduced the bug).
4. **Fix.** Propose the change, explain why, get approval before writing.
5. **Verify.** Re-run the exact reproduction command. Only mark_todo "completed" with the exit code/output as evidence.
6. **Stop condition.** Don't call this done until get_todos shows zero pending/in_progress.