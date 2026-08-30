---
name: Virtual Tours
description: Build multi-scene 360° virtual tours with scene-switch hotspots and live camera state
endpoint: /components/tours
category: Panoramas
order: 1
package: dash_pannellum
icon: mdi:map-marker-path
lastmod: 2026-06-15
---

.. llms_copy::Virtual Tours

.. toc::

### Overview

A tour is a dictionary of **scenes** plus a `default` block that picks the first scene. Each scene is a Pannellum scene configuration: an equirectangular `panorama` URL, an initial camera (`pitch`, `yaw`, `hfov`), and optional `hotSpots`.

Hotspots with `"type": "scene"` switch to another scene when clicked — that's what turns a set of panoramas into a guided tour. `sceneFadeDuration` crossfades the transition.

---

### Live example

Click the hotspot on the horizon to jump between scenes — and watch `currentScene`, `pitch` and `yaw` stream into the Dash callback below the viewer.

Scene jumps here are a clean crossfade with no "Loading…" flash: since 0.2.0 the component **prefetches every other scene's panorama** once the viewer is up (`preloadScenes`, on by default), and this example also sets `hideLoadingSpinner=True` so the load box never appears even on a cold cache:

.. exec::docs.tours.tour_example
    :code: false

.. source::docs/tours/tour_example.py
    :defaultExpanded: false
    :withExpandedButton: true

---

### Scene configuration

The most useful per-scene keys (all standard Pannellum options):

| Key | Type | Description |
|-----|------|-------------|
| `panorama` | str | URL of the equirectangular image |
| `title` | str | Shown in the viewer's title bar |
| `hfov` | number | Initial horizontal field of view, degrees |
| `pitch` / `yaw` | number | Initial camera orientation |
| `autoLoad` | bool | Load this scene without a click |
| `hotSpots` | list | Scene-switch and info hotspots |

A scene-switch hotspot:

```python
{
    "pitch": -2.1,          # where the hotspot sits in the panorama
    "yaw": 132.9,
    "type": "scene",        # makes it a navigation hotspot
    "text": "Next room",    # tooltip
    "sceneId": "kitchen",   # scene to load on click
    "targetYaw": -23,       # optional: camera orientation after the jump
    "targetPitch": 2,
}
```

.. admonition::Authoring hotspot positions
    :icon: mdi:crosshairs-gps
    :color: blue

    Set `showCenterDot=True` and read `pitch`/`yaw` from a callback while aiming the dot at your target — the [Callback Hotspots](/components/hotspots) page demonstrates this workflow.

---

### Tracking the active scene

`currentScene` updates whenever the user navigates, so you can drive any output from tour progress — breadcrumbs, maps, info panels:

```python
@callback(
    Output("scene-info", "children"),
    Input("tour-demo", "currentScene"),
)
def describe(scene):
    return SCENE_DESCRIPTIONS.get(scene, "")
```
