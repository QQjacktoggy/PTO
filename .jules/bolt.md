# Bolt's Performance Journal

This journal documents critical, codebase-specific performance insights, patterns, and lessons learned to avoid repeating past mistakes and make faster, more informed decisions in future optimizations.

## 2025-02-15 - PyYAML Performance and CSafeLoader/CSafeDumper
**Learning:** PyYAML's default pure-Python `safe_load` and `safe_dump` are highly CPU-intensive and can cause significant latency in environments where YAML configuration files are parsed frequently (e.g. CLI tool startup, configuration validation, test suites). Utilizing the conditionally imported C-based `CSafeLoader` and `CSafeDumper` yields a ~7.8x improvement in load times, a ~4.8x improvement in dump times, and decreases test suite latency by over 60%.
**Action:** Always check if fast C-based loaders (`CSafeLoader`) and dumpers (`CSafeDumper`) are available when working with PyYAML, and define custom `FastSafeLoader` and `FastSafeDumper` aliases with graceful fallback to standard `SafeLoader`/`SafeDumper`.
