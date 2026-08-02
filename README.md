<div align="center">

<a href="https://2plot.ai">
  <img src="https://cdn.2plot.ai/github_assets/light_mode_2plot.png" alt="2plot.ai" width="320">
</a>

# dash-pannellum — 360° panoramas for Dash

**Interactive 360° panoramas, virtual tours, multi-resolution tiles and 360° video
for Plotly Dash 4.**

Built on [Pannellum](https://pannellum.org/) — the plug-in-free WebGL panorama
viewer — wrapped as a single Dash component with a real-time imperative API.

[![PyPI](https://img.shields.io/pypi/v/dash-pannellum?color=1c7ed6)](https://pypi.org/project/dash-pannellum/)
[![Python](https://img.shields.io/pypi/pyversions/dash-pannellum)](https://pypi.org/project/dash-pannellum/)
[![Dash](https://img.shields.io/badge/dash-%E2%89%A54.2-119DFF)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Docs](https://img.shields.io/badge/docs-pannellum.2plot.dev-1c7ed6)](https://pannellum.2plot.dev)

**[Documentation](https://pannellum.2plot.dev)** ·
[PyPI](https://pypi.org/project/dash-pannellum/) ·
[Changelog](./CHANGELOG.md) ·
[Discord](https://discord.gg/WEnZR35mrK)

</div>

---

This repository is two things at once: the **component package** (`dash_pannellum`,
published to PyPI) and its **documentation site** — a markdown-driven Dash app where
every example is live, deployed at [pannellum.2plot.dev](https://pannellum.2plot.dev)
as a [2plot network](https://2plot.dev) satellite. The site doubles as the
component's test bed.

![dash-pannellum — interactive 360° panoramas in a Dash app](https://cdn.2plot.ai/github_assets/Screenshot%202026-06-18%20at%2011.28.52%E2%80%AFAM.png)

## Install

```bash
pip install dash-pannellum
```

Python 3.9+ and Dash 4.2+. The component's own bundle ships inside the package; the
Pannellum 2.5 viewer (and video.js, for 360° video) load from their CDNs at runtime,
with one shared load no matter how many viewers are on the page.

## Quick start

```python
import dash
from dash import html
from dash_pannellum import DashPannellum

app = dash.Dash(__name__)

app.layout = html.Div(
    DashPannellum(
        id="panorama",
        tour={
            "default": {"firstScene": "alma"},
            "scenes": {
                "alma": {
                    "type": "equirectangular",
                    "panorama": "https://pannellum.org/images/alma.jpg",
                }
            },
        },
        autoLoad=True,
        width="100%",
        height="500px",
    )
)

if __name__ == "__main__":
    app.run(debug=True)
```

## Viewer modes

Pass exactly one of:

| Prop | Mode |
|------|------|
| `tour` | Equirectangular panoramas & multi-scene virtual tours |
| `multiRes` | Tiled multi-resolution (gigapixel) panoramas |
| `video` | 360° video via video.js (optional HLS/DASH with `useHttpStreaming`) |

## Reading the viewer

`pitch`, `yaw`, `hfov`, `currentScene`, `loaded` and `lastClickedHotspot` update
from the viewer — use them as `Input`s. View-state updates are throttled to 4/s and
change-detected, so idle viewers don't fire callbacks.

## Driving the viewer in real time

The camera and the scene are imperative — no teardown, no rebuild, no flash:

| Prop | What it does |
|------|--------------|
| `lookAt` | Write `{pitch, yaw, hfov, animated}` to pan/zoom the live viewer — smooth enough for joystick steering via `set_props` |
| `loadScene` | Switch tour scenes in place |
| `callbackHotspots` | Clickable hotspots that report their `name` back to Dash; prop changes diff per-name, so markers can drift in real time and stay clickable mid-flight |
| `panoramaCanvasId` | Point a tour scene at a `<canvas>` and redraw it to update the sphere's texture in place (`dynamicUpdate` keeps it live every frame) |
| `orientation` | Gyroscope look-around — the device is the camera; `orientationSupported` / `orientationActive` report back |

Changing the configuration props (`tour`, `multiRes`, `video`, `compass`,
`northOffset`, …) re-initializes the viewer cleanly, so panoramas can be swapped
from a callback.

## Documentation

Every page at [pannellum.2plot.dev](https://pannellum.2plot.dev) runs its examples
live:

| Page | What it shows |
|------|---------------|
| [`/getting-started`](https://pannellum.2plot.dev/getting-started) | Install + first panorama |
| [`/components/tours`](https://pannellum.2plot.dev/components/tours) | Multi-scene tours, scene-switch hotspots, live camera state |
| [`/components/scenes`](https://pannellum.2plot.dev/components/scenes) | Scene config playground + the `lookAt` fly-to pattern |
| [`/components/hotspots`](https://pannellum.2plot.dev/components/hotspots) | Callback hotspots + coordinate-authoring workflow |
| [`/components/multires`](https://pannellum.2plot.dev/components/multires) | Tiled gigapixel panoramas |
| [`/components/video`](https://pannellum.2plot.dev/components/video) | 360° video + HTTP streaming |
| [`/components/arena`](https://pannellum.2plot.dev/components/arena) | Joystick-driven 360° arena — tilesets composed into data-URI panoramas |
| [`/components/emotes`](https://pannellum.2plot.dev/components/emotes) | Directed camera motions — shake, knockdown, lunge |
| [`/components/gyro`](https://pannellum.2plot.dev/components/gyro) | Gyroscope steering + a desktop tilt simulator |
| [`/api`](https://pannellum.2plot.dev/api) | Full prop reference, generated from component metadata |

Each page also serves an LLM-ready version at `/<page>/llms.txt` (its prose plus
complete example source), and the site exposes `/llms.txt`, `/sitemap.xml` and
`/robots.txt`. [SKILLS.md](SKILLS.md) is a skills guide to the package — modes,
callback patterns, prop reference and gotchas — written for AI coding assistants
(and humans in a hurry).

## Development

```bash
git clone https://github.com/pip-install-python/dash_pannellum
cd dash_pannellum

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # the docs site's dependencies

# markdown2dash pins gunicorn<22, against the CVE-driven gunicorn>=23 floor in
# requirements.txt. pip cannot resolve both, so it installs without its
# dependency set — everything it actually needs is already in the line above.
pip install --no-deps markdown2dash==0.1.2

pip install -e .                     # the component itself, editable

npm install
npm run build                        # webpack bundle + generated Python classes

python run.py                        # the docs site at http://127.0.0.1:8561
```

`npm run build` writes into `dash_pannellum/` — both the bundle and the generated
`DashPannellum.py`. Both are **committed**: that is what lets `pip install` work
without Node. After a build, restart `run.py` — the docs site imports the package
you just built, so it *is* the integration test.

The docs app's backend is pluggable (Dash 4.4+). Select it in `.env` or the
environment:

```bash
DASH_BACKEND=fastapi python run.py   # ASGI — what production runs
DASH_BACKEND=flask   python run.py   # WSGI default
```

Or with Docker: `docker compose up` (serves on port 8561).

Before opening a PR, run the test suite — it boots the real `run.py` with zero
secrets and checks every registered page, exactly as CI's container job does:

```bash
pytest
```

### Repository layout

```
├── src/lib/                  # React component source
│   ├── components/DashPannellum.react.js
│   └── assets/videojs-pannellum-plugin.js
├── dash_pannellum/           # generated Python package (committed)
├── pyproject.toml            # package metadata (dash>=4.2.0)
├── package.json              # JS build toolchain (webpack 5, babel, react 18)
│
├── run.py                    # documentation app entry point
├── docs/                     # markdown docs + live examples (one folder per page)
├── pages/                    # home + markdown loader + analytics
├── components/               # appshell, header, navbar (dash-mantine-components)
├── lib/                      # backend resolver, network wiring, analytics
├── assets/ templates/        # css/js, index.html with SEO/LLM meta
├── scripts/                  # social-card generator, link audit, smoke tests
├── tests/                    # secretless pytest suite (flask/fastapi/quart)
└── vendor/                   # dash-clerk-auth tarball (docs-site auth, not on PyPI)
```

Adding a docs page means adding a folder under `docs/` — a markdown file plus the
`example.py` files it references — with no Python wiring anywhere else.

### Publish

```bash
npm run build
python -m build              # sdist + wheel from pyproject.toml
twine upload dist/*
```

## Upgrading from 0.0.6

dash-pannellum 0.1.0+ is the modernized revival of the original 0.0.6 component:
Dash 4.2+ / React 18, coherent `customControls` semantics, throttled +
change-detected view-state updates, callback hotspots wired through real Pannellum
click handlers, deduplicated CDN script loading, `pyproject.toml` packaging. See
[CHANGELOG.md](./CHANGELOG.md) for the full history, including everything the
real-time releases (0.2.0–0.4.0) added.

## Credits

- [Pannellum](https://pannellum.org/) by Matthew Petroff — the underlying viewer (MIT)
- [video.js](https://videojs.com/) — 360° video playback
- Documentation shell from the [dash-documentation-boilerplate](https://github.com/pip-install-python/Dash-Documentation-Boilerplate)

## License

MIT — see [LICENSE](./LICENSE). Built by [Pip Install Python](https://github.com/pip-install-python).
