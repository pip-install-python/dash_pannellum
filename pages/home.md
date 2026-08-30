# dash-pannellum — 360° panoramas for Dash

> **`dash-pannellum` — interactive 360° panoramas, virtual tours, multi-resolution tiles and 360° video for Plotly Dash, built on the plug-in-free [Pannellum](https://pannellum.org/) WebGL viewer.** By [Pip Install Python](https://2plot.dev).

dash-pannellum is a lightweight Dash component library that embeds the plug-in-free Pannellum panorama viewer in your Dash apps. Every viewer mode reports its state (pitch, yaw, current scene, clicked hotspots) back to Dash, so your panoramas participate fully in the callback graph.

---

![dash-pannellum — interactive 360° panoramas in a Dash app](https://cdn.2plot.ai/github_assets/Screenshot%202026-06-18%20at%2011.28.52%E2%80%AFAM.png)

## Installation

```bash
pip install dash-pannellum
```

Requires **Dash 4.2+**. The documentation site you are reading is itself a Dash app built with **Dash Mantine Components** — every example on it is live.

## Quickstart

```python
import dash
from dash import html
from dash_pannellum import DashPannellum

app = dash.Dash(__name__)

tour = {
    "default": {"firstScene": "alma"},
    "scenes": {
        "alma": {
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/alma.jpg",
        }
    },
}

app.layout = html.Div(
    DashPannellum(id="panorama", tour=tour, autoLoad=True, width="100%", height="500px")
)

if __name__ == "__main__":
    app.run(debug=True)
```

---

## What can it do?

### 🌍 Equirectangular panoramas
Load a single 360° image and pan/zoom it freely — with an optional compass and configurable north offset.

### 🏛 Virtual tours
Define multiple scenes with scene-switch hotspots and fade transitions. The component exposes `currentScene` for callbacks.

### 🧩 Callback hotspots
Place hotspots anywhere in a scene that report clicks back to Dash through the `lastClickedHotspot` prop — build inspection UIs, info panels, shop-the-room experiences.

### 🔭 Multi-resolution tiles
Stream gigapixel panoramas progressively with Pannellum's multires format.

### 🎥 360° video
Play equirectangular video through video.js, with optional HLS/DASH HTTP streaming for live sources.

### 🎛 Live view state
`pitch`, `yaw` and `currentScene` update as the user looks around, so you can drive any Dash output from the camera orientation.

---

## Explore the docs

- **[Getting Started](/getting-started)** — install, first panorama, core props
- **[Virtual Tours](/components/tours)** — multi-scene tours with hotspots
- **[360° Video](/components/video)** — video panoramas and HTTP streaming
- **[Multi-Resolution](/components/multires)** — tiled gigapixel panoramas
- **[Callback Hotspots](/components/hotspots)** — clickable hotspots wired to callbacks
- **[API Reference](/api)** — every prop, documented

---

## Project links

- **GitHub**: [pip-install-python/dash_pannellum](https://github.com/pip-install-python/dash_pannellum)
- **PyPI**: [dash-pannellum](https://pypi.org/project/dash-pannellum/)
- **Pannellum**: [pannellum.org](https://pannellum.org/) — the underlying viewer
- **Community**: [Dash Community Forum](https://community.plotly.com/)
