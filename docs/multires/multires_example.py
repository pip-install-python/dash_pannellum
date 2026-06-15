from dash_pannellum import DashPannellum

component = DashPannellum(
    id="multires-demo",
    multiRes={
        "basePath": "https://pannellum.org/images/multires/library",
        "path": "/%l/%s%y_%x",
        "fallbackPath": "/fallback/%s",
        "extension": "jpg",
        "tileResolution": 512,
        "maxLevel": 6,
        "cubeResolution": 8432,
    },
    autoLoad=True,
    compass=True,
    width="100%",
    height="450px",
)
