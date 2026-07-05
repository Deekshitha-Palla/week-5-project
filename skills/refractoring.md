---
name: refactoring
description: Use when the user wants code restructured, cleaned up, simplified, or reorganized without changing behavior — "clean this up," "simplify," "extract this into a function," "this is messy." Behavior must stay identical; if the user also wants new behavior, that's feature_implementation instead.
---

# Refactoring

## Tools required
Core (always loaded): grep, list_definitions, file tools, run_command

## Workflow
1. **Establish a behavior baseline.** Run existing tests via run_command *before* changing anything — this is the ground truth the refactor must preserve.
2. **Identify the target.** Use grep/list_definitions to find every caller of the code being refactored — a refactor that misses a caller is a bug, not a refactor.
3. **Refactor incrementally.** One structural change at a time (e.g. extract function, then rename, then simplify) — not a single large rewrite.
4. **Re-run tests after each increment.** Confirm identical pass/fail state to the baseline from step 1.
5. **Report.** Note what changed structurally and confirm behavior is unchanged (test results before/after).

## Stop condition
Test suite results after refactor are identical to the step-1 baseline.