# Bolt's Journal - Critical Learnings Only

## 2026-07-28 - PyYAML parser optimization with CSafeLoader
**Learning:** PyYAML's default pure-Python `safe_load` parser is a significant bottleneck when parsing several configuration files in rapid succession (e.g., during startup, CLI execution, or test suite run). In this codebase, configuring C-based `CSafeLoader` and `CDumper` provides a ~7.8x speedup on YAML parsing tasks, lowering test collection and execution time from ~1.74s to ~0.56s.
**Action:** Always conditionally import C-extensions for performance-sensitive standard libraries like PyYAML (specifically `CSafeLoader` and `CDumper`) with a graceful fallback to `SafeLoader`/`Dumper` for portability.
