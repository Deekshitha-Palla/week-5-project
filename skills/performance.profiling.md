---
name: performance_profiling
description: Use when the user reports something is slow, asks to "optimize," "speed up," or "reduce latency/memory." Requires profiling data before any optimization — do not propose speed fixes based on code inspection alone.
---

# Performance Profiling

## Tools required
Core (always loaded): run_command, file tools

## Workflow
1. **Reproduce the slowness with a measurement**, not a guess — run_command with timing/profiling (e.g. `python -m cProfile`, `time`, or the project's existing benchmark if one exists).
2. **Identify the actual bottleneck** from profiler output — the slowest function by cumulative time, not the one that "looks" inefficient.
3. **Baseline.** Record the current measurement before changing anything.
4. **Optimize the identified bottleneck only** — resist fixing unrelated code that merely looks suboptimal.
5. **Re-measure with the same method as step 1** and compare to the baseline.

## Stop condition
A quantified before/after measurement exists showing improvement — "this should be faster" is never sufficient, only measured numbers are.