import dash_mantine_components as dmc
from dash import Input, Output, callback, html

from dash_pannellum import DashPannellum

tour = {
    "default": {
        "firstScene": "observatory",
        "sceneFadeDuration": 1000,
        "author": "Pip Install Python",
    },
    "scenes": {
        "observatory": {
            "title": "ALMA Observatory",
            "hfov": 110,
            "pitch": -3,
            "yaw": 117,
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/alma.jpg",
            "autoLoad": True,
            "hotSpots": [
                {
                    "pitch": -2.1,
                    "yaw": 132.9,
                    "type": "scene",
                    "text": "Travel to Cerro Toco",
                    "sceneId": "desert",
                }
            ],
        },
        "desert": {
            "title": "Cerro Toco",
            "hfov": 110,
            "yaw": 5,
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/cerro-toco-0.jpg",
            "hotSpots": [
                {
                    "pitch": -0.6,
                    "yaw": 37.1,
                    "type": "scene",
                    "text": "Back to the observatory",
                    "sceneId": "observatory",
                    "targetYaw": -23,
                    "targetPitch": 2,
                }
            ],
        },
    },
}

component = html.Div(
    [
        DashPannellum(
            id="tour-demo",
            tour=tour,
            autoLoad=True,
            compass=True,
            # 0.2.0: scenes are prefetched (preloadScenes defaults True) and
            # the load box is suppressed, so hotspot jumps are a clean fade.
            hideLoadingSpinner=True,
            width="100%",
            height="450px",
        ),
        dmc.Group(
            [
                dmc.Badge("—", id="tour-demo-scene", size="lg", variant="light"),
                dmc.Code("waiting for camera…", id="tour-demo-view"),
            ],
            mt="md",
            gap="md",
        ),
    ]
)


@callback(
    Output("tour-demo-scene", "children"),
    Output("tour-demo-view", "children"),
    Input("tour-demo", "currentScene"),
    Input("tour-demo", "pitch"),
    Input("tour-demo", "yaw"),
)
def show_camera_state(scene, pitch, yaw):
    view = f"pitch {pitch or 0:+.1f}° · yaw {yaw or 0:+.1f}°"
    return scene or "—", view
