import dash_mantine_components as dmc
from dash import Input, Output, callback, html

from dash_pannellum import DashPannellum

HOTSPOT_INFO = {
    "telescope-array": "The ALMA antennas sit at 5,000 m on the Chajnantor plateau.",
    "snowy-peaks": "The Andes ridge line, looking east toward Bolivia.",
}

component = html.Div(
    [
        DashPannellum(
            id="hotspot-demo",
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
                        "hfov": 110,
                    }
                },
            },
            callbackHotspots={
                "alma": [
                    {
                        "pitch": -1.2,
                        "yaw": 122.0,
                        "type": "info",
                        "text": "Telescope array",
                        "name": "telescope-array",
                    },
                    {
                        "pitch": 1.5,
                        "yaw": 60.0,
                        "type": "info",
                        "text": "Snowy peaks",
                        "name": "snowy-peaks",
                    },
                ]
            },
            showCenterDot=True,
            autoLoad=True,
            width="100%",
            height="450px",
        ),
        dmc.Alert(
            "Click a hotspot in the panorama…",
            id="hotspot-demo-alert",
            title="Nothing clicked yet",
            color="gray",
            mt="md",
        ),
        dmc.Code("aim the center dot to author coordinates", id="hotspot-demo-aim", mt="sm"),
    ]
)


@callback(
    Output("hotspot-demo-alert", "children"),
    Output("hotspot-demo-alert", "title"),
    Output("hotspot-demo-alert", "color"),
    Input("hotspot-demo", "lastClickedHotspot"),
    prevent_initial_call=True,
)
def on_hotspot_click(name):
    detail = HOTSPOT_INFO.get(name, "No description on file.")
    return detail, f"You clicked: {name}", "teal"


@callback(
    Output("hotspot-demo-aim", "children"),
    Input("hotspot-demo", "pitch"),
    Input("hotspot-demo", "yaw"),
)
def show_aim(pitch, yaw):
    return f'"pitch": {pitch or 0:.1f}, "yaw": {yaw or 0:.1f}  ← center dot position'
