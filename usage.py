import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_pannellum

app = dash.Dash(__name__)

tour_config = {
    "default": {
        "firstScene": "circle",
        "author": "Pip Install Python",
        "sceneFadeDuration": 1000,
    },
    "scenes": {
        "circle": {
            "title": "Dash Pannellum",
            "hfov": 110,
            "pitch": -3,
            "yaw": 117,
            "type": "equirectangular",
            "panorama": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Panoramica_di_piazza_Garibaldi_-_Palagonia.jpg/1600px-Panoramica_di_piazza_Garibaldi_-_Palagonia.jpg",
            "autoLoad": True,  # Add this line to each scene
            "hotSpots": [
                {
                    "pitch": -2.1,
                    "yaw": 132.9,
                    "type": "scene",
                    "text": "Spring House or Dairy",
                    "sceneId": "house"
                }
            ]
        },
        "house": {
            "title": "Spring House or Dairy",
            "hfov": 110,
            "yaw": 5,
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/bma-0.jpg",
            # "autoLoad": True,  # Add this line to each scene
            "hotSpots": [
                {
                    "pitch": -0.6,
                    "yaw": 37.1,
                    "type": "scene",
                    "text": "Mason Circle",
                    "sceneId": "circle",
                    "targetYaw": -23,
                    "targetPitch": 2
                }
            ]
        }
    }
}

multiRes_config = {
    "basePath": "https://pannellum.org/images/multires/library",
    "path": "/%l/%s%y_%x",
    "fallbackPath": "/fallback/%s",
    "extension": "jpg",
    "tileResolution": 512,
    "maxLevel": 6,
    "cubeResolution": 8432,
}

video_config = {
    "sources": [
        {"src": "https://bitmovin-a.akamaihd.net/content/playhouse-vr/progressive.mp4", "type": "video/mp4"},
    ],
    "poster": "https://bitmovin-a.akamaihd.net/content/playhouse-vr/poster.jpg"
}

app.layout = html.Div([
    html.H1("Tour Example"),
    dash_pannellum.DashPannellum(
        id='tour-component',
        tour=tour_config,
        customControls=True,
        showCenterDot=True,
        width='100%',
        height='400px',
        autoLoad=False,
        compass=True,
        northOffset=90
    ),
    html.Div(id='tour-output'),
    html.Hr(),
    html.H1("Multiresolution Example"),
    dash_pannellum.DashPannellum(
        id='multires-component',
        multiRes=multiRes_config,
        customControls=True,
        showCenterDot=True,
        autoLoad=False,
        width='100%',
        height='400px',
        compass=True,
        northOffset=90
    ),
    html.Div(id='multires-output'),
    html.Hr(),
    html.H1("Video Panorama Example"),
    dash_pannellum.DashPannellum(
        id='video-component',
        video=video_config,
        showCenterDot=True,
        autoLoad=False,
        width='100%',
        height='400px',
        compass=True,
        northOffset=90
    ),
    dcc.Interval(id='interval-component', interval=100, n_intervals=0)
])


if __name__ == '__main__':
    app.run_server(debug=True, port='8051')
