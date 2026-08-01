# Bolt's Journal - Critical Learnings Only

## 2025-02-15 - Fast YAML Loading with PyYAML and LibYAML
**Learning:** PyYAML's default `yaml.safe_load` uses a pure-Python loader (`SafeLoader`) which is extremely slow when reading multiple configuration files repeatedly. PyYAML has a fast C-based loader `CSafeLoader` when compiled with `libyaml` support, which can be aliased as a fast loader. Standardizing on `yaml.load(..., Loader=CSafeLoader)` (with fallback to `SafeLoader`) improves config loading time by ~74% (from ~73.6ms to ~19.3ms) and test execution time significantly.
**Action:** Always conditionally import `CSafeLoader` as `FastSafeLoader` and fallback to `SafeLoader`, then use it for loading configuration YAMLs.
