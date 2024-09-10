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
        autoLoad=False
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
    ),
    html.Div(id='video-output'),
    dcc.Interval(id='interval-component', interval=100, n_intervals=0)
])


@app.callback(
    Output('tour-output', 'children'),
    Input('tour-component', 'pitch'),
    Input('tour-component', 'yaw'),
    Input('tour-component', 'currentScene'),
    Input('interval-component', 'n_intervals')
)
def update_tour_output(pitch, yaw, current_scene, n):
    if pitch is not None and yaw is not None and current_scene is not None:
        return f'Current Scene: {current_scene}, Camera Position - Pitch: {pitch:.2f}, Yaw: {yaw:.2f}'
    return 'Loading tour...'

@app.callback(
    Output('multires-output', 'children'),
    Input('multires-component', 'pitch'),
    Input('multires-component', 'yaw'),
    Input('interval-component', 'n_intervals')
)
def update_multires_output(pitch, yaw, n):
    if pitch is not None and yaw is not None:
        return f'Camera Position - Pitch: {pitch:.2f}, Yaw: {yaw:.2f}'
    return 'Loading multiresolution panorama...'

@app.callback(
    Output('video-output', 'children'),
    Input('video-component', 'pitch'),
    Input('video-component', 'yaw'),
    Input('interval-component', 'n_intervals')
)
def update_video_output(pitch, yaw, n):
    if pitch is not None and yaw is not None:
        return f'Camera Position - Pitch: {pitch:.2f}, Yaw: {yaw:.2f}'
    return 'Camera Position - Pitch: 0.00, Yaw: 0.00'

if __name__ == '__main__':
    app.run_server(debug=True)
