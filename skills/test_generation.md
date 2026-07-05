---
name: test_generation
description: Use when the user asks to write tests, add test coverage, or asks "is this tested," "write tests for X." Not for running/debugging existing tests (that's bug_investigation).
---

# Test Generation

## Tools required
Core (always loaded): file tools, run_command, list_definitions

## Workflow
1. **Identify untested behavior.** Use list_definitions + grep on the existing test directory to see what's already covered — don't duplicate existing tests.
2. **Enumerate cases.** For the target function/module: happy path, edge cases (empty/null/boundary input), and known failure modes.
3. **Match existing test conventions.** Check how existing tests in the repo are structured (framework, fixtures, naming) — new tests should look like they belong.
4. **Write tests.**
5. **Run and confirm.** Execute the new tests via run_command — every new test must actually run and pass (or intentionally fail if testing a known bug) before being reported as done.

## Stop condition
All new tests execute successfully via run_command with the expected pass/fail result.
