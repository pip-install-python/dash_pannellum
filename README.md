## Dash Pannellum
Dash Pannellum is a Dash component that integrates the Pannellum panorama viewer into your Dash applications. It allows you to display interactive 360° panoramas, including equirectangular images, cube maps, and 360° videos.
Features

- Display equirectangular panoramas
- Support for multi-resolution panoramas
- 360° video playback
- Tour mode with multiple scenes and hotspots
- Customizable controls
- Center dot option for orientation

### Installation
`pip install dash-pannellum`

### Usage
Here's a simple example of how to use the DashPannellum component:
    
```python
import dash
from dash import html
import dash_pannellum

app = dash.Dash(__name__)

app.layout = html.Div([
    dash_pannellum.DashPannellum(
        id='panorama',
        tour={
            "default": {
                "firstScene": "scene1",
                "sceneFadeDuration": 1000
            },
            "scenes": {
                "scene1": {
                    "title": "Example Panorama",
                    "hfov": 110,
                    "pitch": -3,
                    "yaw": 117,
                    "type": "equirectangular",
                    "panorama": "https://pannellum.org/images/from-tree.jpg"
                }
            }
        },
        width='100%',
        height='400px',
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
```
### Component Properties

- `id` (string): The ID used to identify this component in Dash callbacks.
- `width` (string): The width of the panorama viewer.
- `height` (string): The height of the panorama viewer.
- `tour` (dict): Configuration object for the tour mode.
- `multiRes` (dict): Configuration object for multi-resolution panoramas.
- `video` (dict): Configuration object for video panoramas.
- `customControls` (boolean): If true, enables custom controls for the panorama viewer.
- `showCenterDot` (boolean): If true, displays a center dot in the panorama viewer.
- `loaded` (boolean; read-only): Indicates whether the panorama has been loaded.
- `pitch` (number; read-only): The current pitch of the panorama view.
- `yaw` (number; read-only): The current yaw of the panorama view.
- `currentScene` (string; read-only): The ID of the current scene in tour mode.

## Examples
___
### Tour Mode
```python
tour_config = {
    "default": {
        "firstScene": "scene1",
        "sceneFadeDuration": 1000
    },
    "scenes": {
        "scene1": {
            "title": "First Scene",
            "hfov": 110,
            "pitch": -3,
            "yaw": 117,
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/from-tree.jpg",
            "hotSpots": [
                {
                    "pitch": -2.1,
                    "yaw": 132.9,
                    "type": "scene",
                    "text": "Go to Second Scene",
                    "sceneId": "scene2"
                }
            ]
        },
        "scene2": {
            "title": "Second Scene",
            "hfov": 110,
            "yaw": 5,
            "type": "equirectangular",
            "panorama": "https://pannellum.org/images/bma-0.jpg",
            "hotSpots": [
                {
                    "pitch": -0.6,
                    "yaw": 37.1,
                    "type": "scene",
                    "text": "Go to First Scene",
                    "sceneId": "scene1",
                    "targetYaw": -23,
                    "targetPitch": 2
                }
            ]
        }
    }
}

dash_pannellum.DashPannellum(
    id='tour-component',
    tour=tour_config,
    width='100%',
    height='400px',
)
```
### Partial Panorama
Partial panoramas can be displayed by specifying the extents of the equirectangular panorama using the haov, vaov, and vOffset parameters. These parameters define the horizontal angle of view, vertical angle of view, and vertical offset, respectively.
```python
partial_panorama_config = {
    "type": "equirectangular",
    "panorama": "https://pannellum.org/images/charles-street.jpg",
    "haov": 149.87,
    "vaov": 54.15,
    "vOffset": 1.17
}

dash_pannellum.DashPannellum(
    id='partial-panorama-component',
    tour={"default": {"firstScene": "scene1"}, "scenes": {"scene1": partial_panorama_config}},
    width='100%',
    height='400px',
)
```
In this example:

- `haov`: 149.87 degrees - Specifies the horizontal angle of view.
- `vaov`: 54.15 degrees - Specifies the vertical angle of view.
- `vOffset`: 1.17 degrees - Specifies the vertical offset of the panorama.

These parameters allow you to display panoramas that don't cover a full 360° horizontally or 180° vertically. The vOffset parameter is particularly useful when the panorama is not centered vertically.
### Multi-resolution Panorama
```python
multiRes_config = {
    "basePath": "https://pannellum.org/images/multires/library",
    "path": "/%l/%s%y_%x",
    "fallbackPath": "/fallback/%s",
    "extension": "jpg",
    "tileResolution": 512,
    "maxLevel": 6,
    "cubeResolution": 8432
}

dash_pannellum.DashPannellum(
    id='multires-component',
    multiRes=multiRes_config,
    width='100%',
    height='400px',
)
```
### Video Panorama
```python
video_config = {
    "sources": [
        {"src": "https://bitmovin-a.akamaihd.net/content/playhouse-vr/progressive.mp4", "type": "video/mp4"},
    ],
    "poster": "https://bitmovin-a.akamaihd.net/content/playhouse-vr/poster.jpg"
}

dash_pannellum.DashPannellum(
    id='video-component',
    video=video_config,
    width='100%',
    height='400px',
)
```
### Callbacks
You can use Dash callbacks to interact with the component. Here's an example that updates an output based on the panorama's current state:
python
```python
from dash.dependencies import Input, Output

@app.callback(
    Output('output-div', 'children'),
    Input('panorama', 'loaded'),
    Input('panorama', 'pitch'),
    Input('panorama', 'yaw'),
    Input('panorama', 'currentScene')
)
def update_output(loaded, pitch, yaw, current_scene):
    if loaded and pitch is not None and yaw is not None:
        return f'Current Scene: {current_scene}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}'
    return 'Loading panorama...'
```
### Contributing
Contributions to dash-pannellum are welcome! Please refer to the project's issues on GitHub for any feature requests or bug reports.

### License
This project is licensed under the MIT License.