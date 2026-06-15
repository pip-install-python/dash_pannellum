import dash_mantine_components as dmc
from dash import Input, Output, State, clientside_callback, html

from dash_pannellum import DashPannellum

# The quick sheet — keys must match window.CAM_EMOTES.SHEET
# (assets/camera_emotes.js), which owns the keyframe timelines.
EMOTES = {
    "shake": "🫨 Shake",
    "knockdown": "🪦 Hit the floor",
    "lunge": "⚔️ Lunge",
    "dizzy": "😵 Dizzy",
    "scan": "👀 Scan",
    "flinch": "🤕 Flinch",
}

component = html.Div(
    [
        DashPannellum(
            id="emote-pano",
            tour={
                "default": {"firstScene": "springhouse"},
                "scenes": {
                    "springhouse": {
                        "title": "Spring House",
                        "type": "equirectangular",
                        "panorama": "https://pannellum.org/images/bma-0.jpg",
                        "autoLoad": True,
                        "yaw": 5,
                        "pitch": 0,
                        "hfov": 95,
                        # Leave headroom for the emotes' hfov kicks
                        "minHfov": 45,
                        "maxHfov": 115,
                    }
                },
            },
            autoLoad=True,
            width="100%",
            height="420px",
        ),
        dmc.Group(
            [
                dmc.Button(
                    label,
                    id=f"emote-btn-{name}",
                    variant="light",
                    size="xs",
                )
                for name, label in EMOTES.items()
            ],
            mt="md",
            gap="xs",
            wrap="wrap",
        ),
        dmc.Alert(
            "Look anywhere in the scene, then trigger an emote — every motion "
            "plays relative to your current gaze.",
            id="emote-status",
            color="gray",
            mt="sm",
        ),
        dmc.Code("camera idle", id="emote-readout", mt="xs"),
    ]
)

# One clientside callback for the whole sheet: the triggered button picks the
# emote; the pano's reported pitch/yaw/hfov States are the motion's base.
# Playback is pure lookAt sequencing — the server is never involved.
clientside_callback(
    """async function(n1, n2, n3, n4, n5, n6, pitch, yaw, hfov) {
        const trig = window.dash_clientside.callback_context.triggered_id;
        if (!trig) { return window.dash_clientside.no_update; }
        const name = String(trig).replace('emote-btn-', '');
        return await window.CAM_EMOTES.play('emote-pano', name, {
            pitch: pitch, yaw: yaw, hfov: hfov,
        });
    }""",
    Output("emote-status", "children"),
    [Input(f"emote-btn-{name}", "n_clicks") for name in EMOTES],
    State("emote-pano", "pitch"),
    State("emote-pano", "yaw"),
    State("emote-pano", "hfov"),
    prevent_initial_call=True,
)


# Live camera state, so the motion is legible while it plays.
clientside_callback(
    """function(pitch, yaw, hfov) {
        const f = (v, d) => (typeof v === 'number' ? v.toFixed(d) : '0');
        return 'pitch ' + f(pitch, 1) + '\\u00b0 \\u00b7 yaw ' + f(yaw, 1)
            + '\\u00b0 \\u00b7 hfov ' + f(hfov, 0) + '\\u00b0';
    }""",
    Output("emote-readout", "children"),
    Input("emote-pano", "pitch"),
    Input("emote-pano", "yaw"),
    Input("emote-pano", "hfov"),
)
