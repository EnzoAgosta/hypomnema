---
title: Installation
---

# Installation

## Requirements

- Python 3.13 or later

## Install from PyPI

```bash
pip install hypomnema
```

## Verify Installation

```python
import hypomnema as hm
print(hm.__version__)
```

## Optional: lxml Backend

For better performance on large files (3-5x faster), install with lxml:

```bash
pip install hypomnema[lxml]
```

Or install lxml separately:

```bash
pip install lxml>=6.0.2
```

Hypomnema will automatically use lxml when available.

## Next Steps

Now that hypomnema is installed, let's [load your first TMX file](/en/tutorial/02-your-first-tmx).
