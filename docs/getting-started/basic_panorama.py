from dash_pannellum import DashPannellum

component = DashPannellum(
    id="gs-basic-panorama",
    tour={
        "default": {"firstScene": "alma", "author": "Pip Install Python"},
        "scenes": {
            "alma": {
                "title": "ALMA Observatory",
                "type": "equirectangular",
                "panorama": "https://pannellum.org/images/alma.jpg",
                "autoLoad": True,
            }
        },
    },
    autoLoad=True,
    compass=True,
    width="100%",
    height="450px",
)
