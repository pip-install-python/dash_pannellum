from dash_pannellum import DashPannellum

component = DashPannellum(
    id="video-demo",
    video={
        "sources": [
            {
                "src": "https://pannellum.org/images/video/jfk.webm",
                "type": "video/webm",
            },
            {
                "src": "https://pannellum.org/images/video/jfk.mp4",
                "type": "video/mp4",
            },
        ],
    },
    autoLoad=True,
    width="100%",
    height="450px",
)
