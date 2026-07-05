---
name: codebase_onboarding
description: Use on first contact with an unfamiliar repo, or when the user asks "what does this codebase do," "where do I start," "give me an overview" before any specific task is named. Runs once per repo, not per task — architecture_analysis is for repeated structural questions afterward.
---

# Codebase Onboarding

## Tools required
Core (always loaded): list_definitions, grep, file tools

## Workflow
1. **Read repo-level docs first.** README, AGENTS.md, CONTRIBUTING.md if present — don't infer from code what's already documented.
2. **Find entry points.** list_definitions on likely entry files; confirm how the project is actually run/started.
3. **Map top-level structure.** Directory-by-directory, one line each on purpose — not file-by-file.
4. **Identify conventions.** Test framework, style/lint config, commit pattern — grep for config files rather than assuming.
5. **Produce output.** Short orientation summary: what it does, how to run it, how to test it, where to start reading. This becomes context for every later skill call, not a one-off report.

## Stop condition
Entry point, test command, and top-level structure are all confirmed by evidence, not assumed from naming conventions.