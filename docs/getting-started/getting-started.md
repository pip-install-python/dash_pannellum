---
name: Getting Started
description: Install Dash Pannellum and embed your first interactive 360° panorama in a Dash app
endpoint: /getting-started
category: Getting started
order: 1
package: dash_pannellum
icon: mdi:rocket-launch-outline
lastmod: 2026-08-16
---

.. llms_copy::Getting Started

.. toc::

### Installation

```bash
pip install dash-pannellum
```

Dash Pannellum targets **Dash 4.2+** and works on every Dash backend (Flask, FastAPI, Quart). The viewer itself — [Pannellum](https://pannellum.org/) — is loaded from its CDN at runtime, so the Python wheel stays tiny and there is nothing else to install.

.. admonition::Reviving a classic
    :icon: mdi:history
    :color: teal

    Dash Pannellum {{VERSION:dash-pannellum}} is the modernized revival of the original 0.0.6 component: rebuilt against Dash 4.x and React 18, documented with the live examples on this site, and repackaged with `pyproject.toml`.

---

### Your first panorama

A single 360° image is just a **tour with one scene**. Set `autoLoad=True` to skip the click-to-load screen and `compass=True` to display a heading indicator:

.. exec::docs.getting-started.basic_panorama

Drag to look around, scroll to zoom, and use the controls in the top-left corner. Everything you see is rendered with WebGL — no browser plug-ins.

---

### The three viewer modes

`DashPannellum` picks its mode from whichever configuration prop you pass:

| Prop | Mode | Use it for |
|------|------|-----------|
| `tour` | Equirectangular scenes | Single panoramas and multi-scene virtual tours |
| `multiRes` | Tiled multi-resolution | Gigapixel panoramas streamed progressively |
| `video` | 360° video (video.js) | Equirectangular video files and HTTP streams |

Each mode has its own documentation page with a live example — see [Virtual Tours](/components/tours), [Multi-Resolution](/components/multires) and [360° Video](/components/video).

---

### Reading the viewer state in callbacks

The component continuously reports the camera orientation back to Dash. Use `pitch`, `yaw` and `currentScene` as callback `Input`s:

```python
from dash import Input, Output, callback

@callback(
    Output("readout", "children"),
    Input("my-panorama", "pitch"),
    Input("my-panorama", "yaw"),
)
def show_view(pitch, yaw):
    return f"Looking at pitch {pitch}°, yaw {yaw}°"
```

Updates are change-detected and throttled to 4 per second, so idle panoramas don't spam your callback graph.

---

### Next steps

- **[Virtual Tours](/components/tours)** — connect multiple scenes with hotspots
- **[Callback Hotspots](/components/hotspots)** — make hotspots fire Dash callbacks
- **[API Reference](/api)** — the full prop table
