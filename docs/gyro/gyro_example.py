import dash_mantine_components as dmc
from dash import Input, Output, callback, clientside_callback, html

from dash_pannellum import DashPannellum

component = html.Div(
    [
        DashPannellum(
            id="gyro-pano",
            tour={
                "default": {"firstScene": "toco"},
                "scenes": {
                    "toco": {
                        "title": "Cerro Toco",
                        "type": "equirectangular",
                        "panorama": "https://pannellum.org/images/cerro-toco-0.jpg",
                        "autoLoad": True,
                        "yaw": 5,
                        "pitch": 0,
                        "hfov": 100,
                    }
                },
            },
            autoLoad=True,
            compass=True,
            width="100%",
            height="420px",
        ),
        dmc.Group(
            [
                dmc.Switch(
                    id="gyro-switch",
                    label="📱 Gyro look-around",
                    checked=False,
                    size="md",
                ),
                dmc.Badge("sensor: checking…", id="gyro-supported", variant="light",
                          color="gray"),
                dmc.Badge("inactive", id="gyro-active", variant="light", color="gray"),
                dmc.Code("camera idle", id="gyro-readout"),
            ],
            mt="md",
            gap="md",
            wrap="wrap",
        ),
        dmc.Group(
            [
                html.Div(
                    html.Div(
                        id="gyro-pad-dot",
                        style={
                            "position": "absolute",
                            "left": "50%",
                            "top": "50%",
                            "width": "16px",
                            "height": "16px",
                            "borderRadius": "50%",
                            "background": "#12B886",
                            "transform": "translate(-50%, -50%)",
                            "pointerEvents": "none",
                            "boxShadow": "0 0 12px rgba(18, 184, 134, 0.8)",
                        },
                    ),
                    id="gyro-pad",
                    style={
                        "position": "relative",
                        "width": "140px",
                        "height": "140px",
                        "borderRadius": "12px",
                        "border": "2px dashed var(--mantine-color-gray-5)",
                        "cursor": "grab",
                        "touchAction": "none",
                        "flexShrink": 0,
                    },
                ),
                dmc.Text(
                    "No motion sensors on this device? Drag the pad — it feeds "
                    "the camera the same continuous lookAt stream a phone's "
                    "gyroscope would. On a phone, flip the switch instead and "
                    "move the device itself.",
                    size="xs",
                    c="dimmed",
                    style={"flex": 1, "minWidth": 220},
                ),
            ],
            mt="md",
            gap="lg",
            align="center",
        ),
    ]
)

# The gyro request MUST be clientside: on iOS, startOrientation triggers the
# DeviceOrientationEvent permission prompt, which Safari only allows inside
# a user-gesture window — a server round-trip would fall outside it.
clientside_callback(
    """function(checked) { return Boolean(checked); }""",
    Output("gyro-pano", "orientation"),
    Input("gyro-switch", "checked"),
    prevent_initial_call=True,
)


@callback(
    Output("gyro-supported", "children"),
    Output("gyro-supported", "color"),
    Output("gyro-active", "children"),
    Output("gyro-active", "color"),
    Input("gyro-pano", "orientationSupported"),
    Input("gyro-pano", "orientationActive"),
)
def gyro_status(supported, active):
    sup = ("sensor: available", "teal") if supported else \
        ("sensor: not on this device", "gray")
    act = ("gyro steering", "teal") if active else ("inactive", "gray")
    return sup[0], sup[1], act[0], act[1]


clientside_callback(
    """function(pitch, yaw) {
        const f = (v) => (typeof v === 'number' ? v.toFixed(1) : '0');
        return 'pitch ' + f(pitch) + '\\u00b0 \\u00b7 yaw ' + f(yaw) + '\\u00b0';
    }""",
    Output("gyro-readout", "children"),
    Input("gyro-pano", "pitch"),
    Input("gyro-pano", "yaw"),
)
