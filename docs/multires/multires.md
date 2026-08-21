---
name: Multi-Resolution
description: Stream gigapixel panoramas progressively with Pannellum's tiled multires format
endpoint: /components/multires
package: dash_pannellum
icon: mdi:grid-large
lastmod: 2026-06-15
---

.. llms_copy::Multi-Resolution

.. toc::

### Overview

Multi-resolution mode streams a panorama as a pyramid of **tiles**, the way slippy maps work: the viewer fetches only the tiles and zoom levels it needs for the current view. That makes gigapixel panoramas load in milliseconds instead of megabytes.

.. exec::docs.multires.multires_example
    :code: false

Zoom in — the picture sharpens as higher-resolution tiles stream in.

.. source::docs/multires/multires_example.py
    :defaultExpanded: false
    :withExpandedButton: true

---

### Configuration

```python
multiRes = {
    "basePath": "https://example.com/my-pano",  # prefix for every tile URL
    "path": "/%l/%s%y_%x",                      # tile URL pattern
    "fallbackPath": "/fallback/%s",             # cube faces for fallback renderer
    "extension": "jpg",
    "tileResolution": 512,
    "maxLevel": 6,
    "cubeResolution": 8432,
}
```

The placeholders in `path`: `%l` zoom level, `%s` cube face (`f`, `b`, `l`, `r`, `u`, `d`), `%x`/`%y` tile coordinates.

---

### Generating the tiles

Pannellum ships a Python tool that converts an equirectangular image into this tile structure:

```bash
git clone https://github.com/mpetroff/pannellum.git
python pannellum/utils/multires/generate.py my-panorama.jpg -o my-pano
```

The generator prints the matching `multiRes` configuration when it finishes — paste it straight into the Dash prop. See the [Pannellum multires documentation](https://pannellum.org/documentation/examples/multiresolution/) for details.
