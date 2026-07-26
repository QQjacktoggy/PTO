# Bolt's Journal

## 2026-03-04 - PyYAML SafeLoader vs CSafeLoader Performance
**Learning:** PyYAML's pure-Python `SafeLoader` is significantly slower (up to 8x) compared to the C-extension-based `CSafeLoader` when parsing configuration files in structured quant systems, even for moderate-sized config files.
**Action:** Use PyYAML's conditionally imported `CSafeLoader` (falling back to `SafeLoader` when LibYAML is not available) to parse configuration files and optimize startup/validation performance.
