---
name: feature_implementation
description: Use when the user wants new functionality added — "add a feature," "implement X," "build support for Y." Not for bug fixes (use bug_investigation) or code cleanup (use refactoring).
---

# Feature Implementation

## Tools required
Core (always loaded): file tools, run_command, add_todos/get_todos/mark_todo
Gated: docs-lookup (MCP/Context7) — if the feature touches a third-party API/library

## Workflow
1. **Clarify scope.** Confirm what's in/out of scope before planning — ambiguous feature requests waste implementation cycles.
2. **Survey existing patterns.** grep/list_definitions for similar existing features — match the codebase's established conventions rather than inventing a new pattern.
3. **Plan.** add_todos: one todo per logical unit of work (e.g. "add endpoint," "add validation," "add tests"), each with a verification command.
4. **Implement incrementally.** Smallest working slice first, verify, then extend — don't write the whole feature before running anything.
5. **Test.** Write/run tests covering the new behavior, not just the happy path.
6. **Verify.** mark_todo "completed" only with passing test/command output as evidence.

## Stop condition
get_todos shows zero pending/in_progress, and the feature's verification command passes.