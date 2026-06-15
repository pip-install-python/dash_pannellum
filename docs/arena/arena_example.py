import dash_gauge as dg
import dash_mantine_components as dmc
from dash import Input, Output, clientside_callback, dcc, html

from dash_pannellum import DashPannellum

component = dmc.Stack(
    [
        html.Div(
            DashPannellum(
                id="arena-pano",
                width="100%",
                height="100%",
                autoLoad=True,
                compass=True,
                hideLoadingSpinner=True,
                # 0.3.0 dynamic-canvas mode: the scene is bound to a <canvas>
                # (panoramaCanvasId) and this keeps the texture refreshing —
                # movement is just redrawing pixels, never a rebuild.
                dynamicUpdate=True,
            ),
            style={
                "width": "100%",
                "aspectRatio": "2 / 1",
                "borderRadius": "8px",
                "overflow": "hidden",
                "background": "#04080f",
            },
        ),
        dmc.Group(
            [
                dg.DashRCJoystick(
                    id="arena-joy",
                    directionCountMode="Nine",
                    baseRadius=70,
                    controllerRadius=32,
                    throttle=110,
                ),
                dmc.Stack(
                    [
                        dmc.SegmentedControl(
                            id="arena-size",
                            value="early",
                            data=[
                                {"value": "early", "label": "3×3 · early"},
                                {"value": "mid", "label": "5×5 · mid"},
                                {"value": "late", "label": "7×7 · late"},
                            ],
                            size="xs",
                        ),
                        dmc.Code("loading arena…", id="arena-hud"),
                        dmc.Text(
                            "Tilt the stick to look (imperative lookAt). Push it to "
                            "the rim to glide: each step redraws the floor tiles "
                            "into the scene's live canvas texture — the viewer is "
                            "never rebuilt, so there is nothing to flash.",
                            size="xs",
                            c="dimmed",
                        ),
                    ],
                    gap="xs",
                    style={"flex": 1, "minWidth": 260},
                ),
            ],
            align="center",
            gap="xl",
            wrap="wrap",
        ),
        dcc.Interval(id="arena-boot", interval=400, max_intervals=1),
    ],
    gap="md",
)

# First paint once the page (and assets/arena360.js) are up.
clientside_callback(
    """async function(n) { return await window.ARENA360.start(); }""",
    Output("arena-hud", "children"),
    Input("arena-boot", "n_intervals"),
    prevent_initial_call=True,
)

# Growth-stage switch: a different native-zoom tile block, same arena.
clientside_callback(
    """async function(stage) { return await window.ARENA360.start(stage); }""",
    Output("arena-hud", "children", allow_duplicate=True),
    Input("arena-size", "value"),
    prevent_initial_call=True,
)

# The joystick: every frame steers the gaze, a full push glides.
clientside_callback(
    """async function(angle, distance) {
        return await window.ARENA360.drive(angle, distance);
    }""",
    Output("arena-hud", "children", allow_duplicate=True),
    Input("arena-joy", "angle"),
    Input("arena-joy", "distance"),
    prevent_initial_call=True,
)
