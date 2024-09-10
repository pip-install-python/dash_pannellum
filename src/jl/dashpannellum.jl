# AUTO GENERATED FILE - DO NOT EDIT

export dashpannellum

"""
    dashpannellum(;kwargs...)

A DashPannellum component.
DashPannellum is a component for displaying panoramic images and videos.
It supports various modes including tours, multi-resolution images, and 360° videos.
Keyword arguments:
- `id` (String; optional): The ID used to identify this component in Dash callbacks.
- `autoLoad` (Bool; optional): If true, automatically loads the panorama without user interaction.
- `currentScene` (String; optional): The ID of the current scene in tour mode.
- `customControls` (Bool; optional): If true, enables custom controls for the panorama viewer.
- `height` (String; optional): The height of the panorama viewer.
- `multiRes` (Dict; optional): Configuration object for multi-resolution panoramas.
- `pitch` (Real; optional): The current pitch of the panorama view.
- `showCenterDot` (Bool; optional): If true, displays a center dot in the panorama viewer.
- `tour` (Dict; optional): Configuration object for the tour mode.
- `video` (optional): Configuration object for video panoramas.. video has the following type: lists containing elements 'sources', 'poster'.
Those elements have the following types:
  - `sources` (required): . sources has the following type: Array of lists containing elements 'src', 'type'.
Those elements have the following types:
  - `src` (String; required)
  - `type` (String; required)s
  - `poster` (String; optional)
- `width` (String; optional): The width of the panorama viewer.
- `yaw` (Real; optional): The current yaw of the panorama view.
"""
function dashpannellum(; kwargs...)
        available_props = Symbol[:id, :autoLoad, :currentScene, :customControls, :height, :multiRes, :pitch, :showCenterDot, :tour, :video, :width, :yaw]
        wild_props = Symbol[]
        return Component("dashpannellum", "DashPannellum", "dash_pannellum", available_props, wild_props; kwargs...)
end

