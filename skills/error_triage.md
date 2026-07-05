---
name: error_triage
description: Use when an error/exception/traceback appears and the fix approach isn't yet obvious. Trigger before bug_investigation when the error type itself is unclear — syntax error, logic bug, missing dependency, or environment/config issue all need different next steps.
---

# Error Triage

## Tools required
Core (always loaded): run_command, grep, file tools

## Workflow
1. **Read the traceback fully, bottom to top.** Identify the exact exception type and the last frame that's actually in the user's code (not a library internal).
2. **Classify.**
   - SyntaxError/IndentationError → syntax, fix directly
   - ImportError/ModuleNotFoundError → dependency, check requirements/installed packages
   - AssertionError/wrong output, no crash → logic, route to bug_investigation
   - Works locally but fails elsewhere → environment, check versions/config/paths
3. **Confirm classification with evidence.** run_command to reproduce; grep for the failing import/symbol to confirm it's actually missing vs. misnamed.
4. **Route.** Dependency → dependency_audit. Logic → bug_investigation. Environment → check config/env vars directly. Syntax → fix and verify.

## Stop condition
Error type is confirmed by reproduction (not guessed from message text alone) and handed to the correct next skill or fixed directly.