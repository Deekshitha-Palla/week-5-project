---
name: architecture_analysis
description: Use when the user asks how the codebase is structured, how modules/components interact, wants a system overview, or asks questions like "how does X talk to Y," "walk me through this codebase," "what's the data flow," or "explain the design." Trigger even without the word "architecture."
---

# Architecture Analysis

## Tools required
Core (always loaded): grep, list_definitions, file tools
Gated (load if needed): docs-lookup (MCP/Context7) — only if a third-party library's documented interface is part of the question

## Workflow
1. **Locate entry points.** Use list_definitions on likely entry files (main.py, __init__.py, app.py, or whatever the repo's convention is) to find where execution starts.
2. **Map components.** Use grep for class/module definitions and imports to build a list of major components — name + one-line responsibility for each.
3. **Trace dependencies.** For each component, grep its imports/calls to identify which other components it depends on. Note the direction (A calls B, not the reverse).
4. **Trace one representative control flow.** Pick the most central path (e.g. a typical request/task lifecycle) and follow it function-to-function using list_definitions + file reads, in execution order.
5. **Produce output.** Deliver: (a) component list with responsibilities, (b) a dependency relationship (text or simple diagram), (c) the traced control flow as a numbered sequence. Omit components/files not relevant to the question — don't dump the whole repo.
6. **Prioritize entry points over search hits.** Before reading arbitrary files from grep results, read the package's `__init__.py`/main entry point first to see which modules are actually exported/central — a class appearing in many grep matches isn't necessarily architecturally important; one that's exported in `__init__.py` usually is.
7. **Trace, don't list.** When explaining "how something works," follow the actual call chain from the public entry point (e.g. `requests.get()`) function-by-function, citing file:line at each step, until you hit an external dependency or the question is answered. Present as a numbered sequence: "1. `requests.get()` in api.py:73 calls `Session.request()`..." — not a list of files with one-line summaries each.

## Stop condition
Every component named in step 2 appears in either the dependency map or is explicitly noted as a leaf with no outgoing dependencies.














<!-- ----------
name: architecture analysis
description: whenever the user asks about the architechtural related prompts, use this skill.
---------

# Architectural analysis

## Trigger conditions
User asks to "architecture" related or "interaction between the models", then use this skill.

## Tools required
Core(loaded always): grep,list_definitions
Gated(loaded only if demanded): docs-lookup (MCP/Context7) — only if the bug involves a third-party library's documented behavior

## Workflow
1. **Identify the entry points** Identify the starting point to complete the task without missing the flow. 
2. **Go through the major components.** Using the grep and list_definitions find the major components of the architecture or modules.Ensure to find the to cover most of the information without missing the valuable inforamtion.
3. **Understand relationship.** Get familiar with the relationship between the files or modules, understand the 
4. **Trace the control flow.** Understand the flow of the files or modules to read the information in order.
5. **Summarize** By extracting the information about the architecture, summarize the entire information effectively excluding the duolicate and unnecessay sentences. -->
