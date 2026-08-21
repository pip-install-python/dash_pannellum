---
name: Callback Hotspots
description: Place clickable hotspots in a panorama that fire Dash callbacks with the hotspot name
endpoint: /components/hotspots
package: dash_pannellum
icon: mdi:cursor-default-click-outline
lastmod: 2026-06-15
---

.. llms_copy::Callback Hotspots

.. toc::

### Overview

Scene hotspots navigate a tour — **callback hotspots talk to your Dash app**. Pass them in the `callbackHotspots` prop (keyed by scene ID, separate from the scene's own `hotSpots`) and every click updates the `lastClickedHotspot` prop with the hotspot's `name`, ready to be used as a callback `Input`.

Use them for info panels, product tags in showrooms, inspection checklists, "shop the room" experiences — anything where a position in the panorama should trigger Python.

---

### Live example

Click either ⓘ hotspot and watch the alert update from a Dash callback. The code line under the alert streams the current camera position — aim the red center dot at a feature and copy the printed `pitch`/`yaw` into your own hotspot config:

.. exec::docs.hotspots.hotspots_example
    :code: false

.. source::docs/hotspots/hotspots_example.py
    :defaultExpanded: false
    :withExpandedButton: true

---

### Configuration

```python
callbackHotspots = {
    "scene-id": [
        {
            "pitch": -1.2,            # position in the panorama
            "yaw": 122.0,
            "type": "info",           # rendered with Pannellum's info styling
            "text": "Telescope array",  # tooltip on hover
            "name": "telescope-array",  # value written to lastClickedHotspot
        },
    ],
}
```

Then wire the callback:

```python
@callback(
    Output("panel", "children"),
    Input("my-panorama", "lastClickedHotspot"),
    prevent_initial_call=True,
)
def on_click(name):
    return f"You clicked {name}"
```

.. admonition::Why a separate prop?
    :icon: mdi:lightbulb-on-outline
    :color: blue

    Scene `hotSpots` live inside the `tour` dictionary and are plain Pannellum config. `callbackHotspots` are merged in by the component, which attaches a real Pannellum `clickHandlerFunc` to each one — something JSON sent from Python cannot express directly.

---

### Drifting hotspots — live position updates

Since 0.3.1 the live `callbackHotspots` diff is **per-name**: a update that
only changes a hotspot's `pitch`/`yaw` moves the *existing* DOM node in
place instead of destroying and recreating it. Contacts can drift every
tick and stay clickable the whole way — try to catch the paramecium:

.. exec::docs.hotspots.drifting_example
    :code: false

.. source::docs/hotspots/drifting_example.py
    :defaultExpanded: false
    :withExpandedButton: true

The diff rules: unchanged hotspots are untouched; position-only changes
mutate in place (the node survives — hover state and all); changing
anything else (`text`, `type`, `cssClass`) recreates that one hotspot;
names that vanish are removed. On an idle viewer the component nudges one
render so moves show immediately; continuously-rendering viewers
(`dynamicUpdate`, `autoRotate`) pick them up anyway.

### Authoring workflow

1. Set `showCenterDot=True` on the component.
2. Stream `pitch`/`yaw` into a readout callback (as in the example above).
3. Aim the dot at the feature you want to tag.
4. Copy the printed values into your `callbackHotspots` entry.
5. Remove the center dot when you ship.
