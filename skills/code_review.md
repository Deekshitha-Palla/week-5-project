-------------
name: code review
description: Use when the user asks for a code review, wants feedback on a diff/PR, asks "is this good," "any issues with this," or wants quality/style/correctness feedback on existing code (not a request to write new code).
-------------

# Code Review

## Trigger condition
When the user asks for "review the code", "optimize the code", "explain the code", "what is the difference in the codes", "pull request", "time and space complexity", use this skill.

## Tools required
ore (always loaded): grep, list_definitions, file tools
Gated: docs-lookup (MCP/Context7) — only to verify a library API is used correctly

## Workflow
1. **Scope the review.** Identify exactly which files/functions changed or are in question — don't review the whole repo unless asked.
2. **Check correctness first.** Read the logic against its stated purpose/docstring. Use grep to find callers and confirm the change doesn't break assumptions they rely on.
3. **Check consistency.** Use list_definitions/grep to compare against existing patterns in the codebase (naming, error handling, structure) — flag deviations, don't impose external style preferences.
4. **Check tests.** Confirm test coverage exists for the changed behavior; note if it doesn't.
5. **Produce output.** Categorize findings: Correctness issues (must fix) / Consistency issues (should fix) / Suggestions (optional). Cite file:line for each. No praise padding, no restating the code back.

## Stop condition
Every changed function has been checked against both its callers and the test suite.    
