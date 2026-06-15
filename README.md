# Dash Pannellum

> Interactive 360° panoramas, virtual tours, multi-resolution tiles and 360° video for [Plotly Dash](https://dash.plotly.com/) — built on the plug-in-free [Pannellum](https://pannellum.org/) WebGL viewer.

This repository is two things at once:

1. **The component package** — `dash_pannellum`, a Dash component library published to PyPI.
2. **Its documentation site** — a markdown-driven Dash app (`run.py`) built on Dash Mantine Components, where every example is live. The site doubles as the component's test bed.

Dash Pannellum 0.1.0 is the modernized revival of the original 0.0.6 component: **Dash 4.2+**, React 18 build, `pyproject.toml` packaging, and a documentation app on the [dash-documentation-boilerplate](https://github.com/pip-install-python/Dash-Documentation-Boilerplate) architecture with first-class AI/LLM + SEO integration.

---

## Install the component

```bash
pip install dash-pannellum
```

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

**Viewer modes** — pass exactly one of:

| Prop | Mode |
|------|------|
| `tour` | Equirectangular panoramas & multi-scene virtual tours |
| `multiRes` | Tiled multi-resolution (gigapixel) panoramas |
| `video` | 360° video via video.js (optional HLS/DASH with `useHttpStreaming`) |

**Callback surface** — `pitch`, `yaw`, `currentScene`, `loaded` and `lastClickedHotspot` update from the viewer; use them as `Input`s. `callbackHotspots` places clickable hotspots that report their `name` back to Dash.

---

## Run the documentation site

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # includes the vendored dash-improve-my-llms 2.0
pip install -e .                  # the component itself, editable
python run.py                     # http://127.0.0.1:8561
```

The backend is pluggable (Dash 4.1+). Select it in `.env` or the environment:

```bash
DASH_BACKEND=fastapi python run.py   # ASGI: websockets, Swagger UI at /docs
DASH_BACKEND=flask   python run.py   # WSGI default
```

Or with Docker: `docker compose up` (serves on port 8561).

### Documentation pages

| Page | What it shows |
|------|---------------|
| `/getting-started` | Install + first panorama |
| `/components/tours` | Multi-scene tour, live pitch/yaw/scene callbacks |
| `/components/video` | 360° video + HTTP streaming |
| `/components/multires` | Tiled gigapixel panoramas |
| `/components/hotspots` | Callback hotspots + coordinate-authoring workflow |
| `/api` | Full prop reference, generated from component metadata |

Each page also serves an LLM-ready version at `/<page>/llms.txt` (dash-improve-my-llms 2.0), and the site exposes `/llms.txt`, `/sitemap.xml` and `/robots.txt`.

---

## Develop the component

The React source lives in `src/lib/`; the built artifacts and generated Python classes land in `dash_pannellum/`.

```bash
npm install                # toolchain (webpack 5, babel, react 18)
source .venv/bin/activate  # dash-generate-components comes from the venv
npm run build              # build:js (webpack) + build:backends (Python classes)
```

After a build, restart `run.py` — the docs site imports the package you just built, so it *is* the integration test. A browser-level check of the docs pages (viewer canvas renders, no console errors) is the quickest smoke test.

### Repository layout

```
├── src/lib/                  # React component source
│   ├── components/DashPannellum.react.js
│   └── assets/videojs-pannellum-plugin.js
├── dash_pannellum/           # generated Python package (committed)
├── pyproject.toml            # package metadata (dash>=4.2.0)
├── package.json              # JS build toolchain
│
├── run.py                    # documentation app entry point
├── docs/                     # markdown docs + live examples (one folder per page)
├── pages/                    # home + markdown loader + analytics
├── components/               # appshell, header, navbar (dash-mantine-components)
├── lib/                      # backend resolver, directives, analytics
├── assets/ templates/        # css/js, index.html with SEO/LLM meta
├── vendor/                   # dash-improve-my-llms 2.0 tarball (not yet on PyPI)
└── legacy/                   # the original 0.0.6 repo, archived untouched
```

### Publish

```bash
npm run build
python -m build              # sdist + wheel from pyproject.toml
twine upload dist/*
```

---

## For AI assistants

[SKILLS.md](SKILLS.md) is a skills guide to the package — modes, callback patterns, prop reference and gotchas — written for AI coding assistants (and humans in a hurry).

## Changes since 0.0.6

See [CHANGELOG.md](CHANGELOG.md). Highlights: Dash 4.2+ / React 18, coherent `customControls` semantics, throttled + change-detected view-state updates, callback hotspots wired through real Pannellum click handlers, deduplicated CDN script loading (multiple viewers per page), modern packaging.

## Credits

- [Pannellum](https://pannellum.org/) by Matthew Petroff — the underlying viewer (MIT)
- [video.js](https://videojs.com/) — 360° video playback

MIT licensed. Built by [pip-install-python](https://github.com/pip-install-python).
