---
name: dependency_audit
description: Use before adding a new package or upgrading an existing one, or when the user asks "is this safe to upgrade," "any conflicts," "check for vulnerabilities in dependencies."
---

# Dependency Audit

## Tools required
Core (always loaded): run_command, file tools
Gated: web_search or MCP search — for CVE/security advisory lookup not available locally

## Workflow
1. **Check current state.** run_command to list installed versions and the dependency file (requirements.txt/package.json/etc.).
2. **Check for conflicts.** Identify other packages that pin/constrain the same dependency — a version bump for one package can break another's constraint.
3. **Check for known vulnerabilities.** Use gated web/MCP search only for the specific package+version in question — don't do a general sweep.
4. **Test in isolation.** Install the change, run the test suite via run_command, before touching the committed dependency file.
5. **Report.** Version change, conflicts found (if any), vulnerability status, test result — human approves before the dependency file is actually updated.

## Stop condition
Test suite passes with the new version and no unresolved version conflicts remain.