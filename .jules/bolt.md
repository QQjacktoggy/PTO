# Bolt's Journal - Critical Learnings

## 2025-08-05 - CSafeLoader Optimization for YAML Loading
**Learning:** PyYAML's default `safe_load` uses standard pure-Python `SafeLoader`, which has extremely high overhead. Conditional import of `CSafeLoader` (implemented in C) aliased as `FastSafeLoader` reduces configuration loading time by ~74% (from ~75.4ms to ~19.3ms) and cuts test suite execution time in half (from ~1.5s to ~0.7s) without compromising readability or safety.
**Action:** Always import and use the fast C-based loader with standard fallback in configuration-heavy systems. Ensure strict typecheck annotations (e.g. `type: ignore[assignment]`) are provided to satisfy Mypy when re-aliasing the imported loader type.
