import dash_mantine_components as dmc
from dash import Input, Output, callback, html

from dash_pannellum import DashPannellum

VIEW_PRESETS = {
    "ridge": {"label": "Sunrise ridge", "pitch": 2, "yaw": 5, "hfov": 90},
    "plateau": {"label": "Across the plateau", "pitch": -8, "yaw": 135, "hfov": 110},
    "zenith": {"label": "Straight up", "pitch": 55, "yaw": 0, "hfov": 100},
}


def build_tour(preset_key, auto_rotate):
    view = VIEW_PRESETS[preset_key]
    return {
        "default": {"firstScene": "toco"},
        "scenes": {
            "toco": {
                # Identity shown in the viewer's info bar
                "title": "Cerro Toco",
                "author": "Pip Install Python",
                # The panorama itself
                "type": "equirectangular",
                "panorama": "https://pannellum.org/images/cerro-toco-0.jpg",
                "autoLoad": True,
                # Initial camera — pitch/yaw/hfov are per-scene config
                "pitch": view["pitch"],
                "yaw": view["yaw"],
                "hfov": view["hfov"],
                # Zoom limits the user can't escape
                "minHfov": 60,
                "maxHfov": 120,
                # Idle cinematics: degrees/second, negative pans the other way
                "autoRotate": auto_rotate or None,
            }
        },
    }


component = html.Div(
    [
        DashPannellum(
            id="sc-pano",
            tour=build_tour("ridge", 0),
            autoLoad=True,
            width="100%",
            height="420px",
        ),
        dmc.Group(
            [
                dmc.Select(
                    id="sc-preset",
                    label="Initial view preset",
                    value="ridge",
                    data=[
                        {"value": k, "label": v["label"]}
                        for k, v in VIEW_PRESETS.items()
                    ],
                    w=220,
                    size="sm",
                ),
                dmc.Stack(
                    [
                        dmc.Text("autoRotate (°/s)", size="sm", fw=500),
                        dmc.Slider(
                            id="sc-rotate",
                            value=0,
                            min=-8,
                            max=8,
                            step=1,
                            w=240,
                            marks=[
                                {"value": -8, "label": "-8"},
                                {"value": 0, "label": "off"},
                                {"value": 8, "label": "8"},
                            ],
                        ),
                    ],
                    gap=4,
                ),
            ],
            mt="md",
            gap="xl",
            align="flex-end",
        ),
    ]
)


@callback(
    Output("sc-pano", "tour"),
    Input("sc-preset", "value"),
    Input("sc-rotate", "value"),
    prevent_initial_call=True,
)
def reconfigure(preset_key, auto_rotate):
    # Config props are LIVE: a new tour re-initializes the viewer with the
    # new scene settings. (For camera-only moves, use `lookAt` instead —
    # see the fly-to example below.)
    return build_tour(preset_key, auto_rotate)
