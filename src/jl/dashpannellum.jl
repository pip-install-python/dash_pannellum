# AUTO GENERATED FILE - DO NOT EDIT

export dashpannellum

"""
    dashpannellum(;kwargs...)

A DashPannellum component.

Keyword arguments:
- `id` (String; optional)
- `currentScene` (String; optional)
- `customControls` (Bool; optional)
- `height` (String; optional)
- `loaded` (Bool; optional)
- `multiRes` (Dict; optional)
- `pitch` (Real; optional)
- `showCenterDot` (Bool; optional)
- `tour` (Dict; optional)
- `video` (optional): . video has the following type: lists containing elements 'sources', 'poster'.
Those elements have the following types:
  - `sources` (required): . sources has the following type: Array of lists containing elements 'src', 'type'.
Those elements have the following types:
  - `src` (String; required)
  - `type` (String; required)s
  - `poster` (String; optional)
- `width` (String; optional)
- `yaw` (Real; optional)
"""
function dashpannellum(; kwargs...)
        available_props = Symbol[:id, :currentScene, :customControls, :height, :loaded, :multiRes, :pitch, :showCenterDot, :tour, :video, :width, :yaw]
        wild_props = Symbol[]
        return Component("dashpannellum", "DashPannellum", "dash_pannellum", available_props, wild_props; kwargs...)
end

