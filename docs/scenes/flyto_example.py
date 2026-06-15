import random

import dash_mantine_components as dmc
from dash import Input, Output, callback, ctx, html, no_update

from dash_pannellum import DashPannellum

# Named places in the scene. A fly-to is just a lookAt with a duration:
# pitch/yaw aim the camera, hfov zooms it, animated eases the whole move.
TARGETS = {
    "telescope-array": {
        "label": "📡 Telescope array",
        "pitch": -1.2,
        "yaw": 122.0,
        "hfov": 55,
        "story": "Dust on the east dishes — camera dispatched to the array.",
    },
    "snowy-peaks": {
        "label": "🏔 Snowy peaks",
        "pitch": 1.5,
        "yaw": 60.0,
        "hfov": 60,
        "story": "Weather alert on the ridge — checking the snow line.",
    },
    "western-ridge": {
        "label": "🌅 Western ridge",
        "pitch": 0.5,
        "yaw": -120.0,
        "hfov": 70,
        "story": "Motion detected on the western approach.",
    },
}


def fly_to(name, animated=1200):
    target = TARGETS[name]
    return {
        "pitch": target["pitch"],
        "yaw": target["yaw"],
        "hfov": target["hfov"],
        "animated": animated,
    }


component = html.Div(
    [
        DashPannellum(
            id="fly-pano",
            tour={
                "default": {"firstScene": "alma"},
                "scenes": {
                    "alma": {
                        "title": "ALMA Observatory",
                        "type": "equirectangular",
                        "panorama": "https://pannellum.org/images/alma.jpg",
                        "autoLoad": True,
                        "yaw": 117,
                        "pitch": -3,
                        "hfov": 100,
                    }
                },
            },
            # The same targets double as clickable hotspots — clicking one
            # also flies the camera to it (see the second callback).
            callbackHotspots={
                "alma": [
                    {
                        "pitch": t["pitch"],
                        "yaw": t["yaw"],
                        "type": "info",
                        "text": t["label"],
                        "name": name,
                    }
                    for name, t in TARGETS.items()
                ]
            },
            autoLoad=True,
            compass=True,
            width="100%",
            height="420px",
        ),
        dmc.Group(
            [
                *[
                    dmc.Button(
                        t["label"],
                        id={"type": "fly-btn", "target": name},
                        variant="light",
                        size="xs",
                    )
                    for name, t in TARGETS.items()
                ],
                dmc.Button(
                    "🚨 Simulate event",
                    id="fly-event",
                    color="red",
                    variant="filled",
                    size="xs",
                ),
            ],
            mt="md",
            gap="xs",
            wrap="wrap",
        ),
        dmc.Alert(
            "Click a target button, a ⓘ hotspot in the scene, or simulate an "
            "event — the camera flies to the spot.",
            id="fly-status",
            color="gray",
            mt="sm",
        ),
        dmc.Code("camera idle", id="fly-readout", mt="xs"),
    ]
)


@callback(
    Output("fly-pano", "lookAt"),
    Output("fly-status", "children"),
    Output("fly-status", "color"),
    Input({"type": "fly-btn", "target": "telescope-array"}, "n_clicks"),
    Input({"type": "fly-btn", "target": "snowy-peaks"}, "n_clicks"),
    Input({"type": "fly-btn", "target": "western-ridge"}, "n_clicks"),
    Input("fly-event", "n_clicks"),
    Input("fly-pano", "lastClickedHotspot"),
    prevent_initial_call=True,
)
def dispatch_camera(*_):
    trigger = ctx.triggered_id

    if trigger == "fly-event":
        # The "external event" pattern: ANY server-side trigger (a websocket
        # message, an Interval poll, a queue consumer…) can output a lookAt
        # to point the panorama at the area of interest.
        name = random.choice(list(TARGETS))
        return fly_to(name, animated=1500), TARGETS[name]["story"], "red"

    if trigger == "fly-pano":
        name = ctx.inputs["fly-pano.lastClickedHotspot"]
        if name not in TARGETS:
            return no_update, no_update, no_update
        return (
            fly_to(name, animated=900),
            f"Centered on {TARGETS[name]['label']}.",
            "teal",
        )

    name = trigger["target"]
    return fly_to(name), f"Flying to {TARGETS[name]['label']}…", "blue"


@callback(
    Output("fly-readout", "children"),
    Input("fly-pano", "pitch"),
    Input("fly-pano", "yaw"),
    Input("fly-pano", "hfov"),
)
def show_camera(pitch, yaw, hfov):
    return (
        f"pitch {pitch or 0:+.1f}° · yaw {yaw or 0:+.1f}° · "
        f"hfov {hfov or 0:.0f}° (zoom)"
    )
