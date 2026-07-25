# Bolt's Journal

## 2025-02-27 - PyYAML Parsing Optimization
**Learning:** Pure-Python PyYAML parsing (`SafeLoader`) is extremely slow, especially when processing numerous medium-to-large configuration files sequentially. By checking for and utilizing `CSafeLoader` (PyYAML's C-extension-based loader) whenever it is available, YAML parsing speeds can increase by roughly 8x, making config loading and startup times significantly faster.
**Action:** Replace `yaml.safe_load(text)` with `yaml.load(text, Loader=yaml.CSafeLoader)` where C-support is available (falling back to `yaml.SafeLoader` if C-extensions are missing).
