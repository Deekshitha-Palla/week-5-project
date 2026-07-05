---
name: git_workflow
description: Use when the user asks to commit, branch, create a PR, or asks about git history/blame. Governs commit granularity and branch strategy — not general shell commands.
---

# Git Workflow

## Tools required
Core (always loaded): run_command, file tools

## Workflow
1. **Check current state first.** run_command `git status` and `git diff` before any commit — never commit blind.
2. **Group by logical change.** One commit per coherent change (one bug fix, one feature slice) — not one commit per file, not one giant commit per session.
3. **Write the commit message from the diff**, not from memory of the request — message must describe what actually changed.
4. **Branch naming/strategy** — follow whatever convention already exists in `git log --oneline -20`; don't impose a new one.
5. **Never force-push or rewrite shared history** without explicit human confirmation.

## Stop condition
`git status` is clean (or intentionally left with explained pending changes) and the commit message accurately reflects `git diff` content.