# Bolt's Journal - Critical Learnings Only

## 2025-02-13 - Fast C-based YAML Parsing with fallback
**Learning:** Pure Python `yaml.safe_load` can be a significant bottleneck when parsing configuration files in high-frequency validation steps or test suites. Standard PyYAML loads the slow pure Python implementation by default, even if the fast LibYAML C-bindings (`CSafeLoader`) are available in the environment. By importing `CSafeLoader` and falling back to standard `SafeLoader`, we can achieve a ~9x speed improvement in configuration loading, which results in a substantial overall test runtime reduction of up to ~58%.
**Action:** Always import `CSafeLoader` dynamically and fall back to `SafeLoader`, assigning them to clear aliases like `FastSafeLoader` to speed up configuration file reading across the codebase.
