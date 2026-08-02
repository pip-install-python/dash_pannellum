"""Render the dash-pannellum icon artwork: a wireframe panorama sphere with
an orbiting 360° rotation arrow, on the brand's rounded teal tile.

This is the source image for the social card's right-hand art
(scripts/make_social_card.py --artwork) and for the favicon set. Drawn with
Pillow at 4x supersampling, so the only dependency is what the card script
already needs.

    python scripts/make_icon_art.py            # writes assets/icon-art.png
    python scripts/make_icon_art.py --favicons # also regenerate assets/favicon/
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TEAL = (18, 184, 134, 255)        # #12B886 — PRIMARY_COLOR / theme-color
TEAL_DEEP = (11, 138, 100, 255)   # sphere body, one step darker
WHITE = (255, 255, 255, 255)
WHITE_SOFT = (255, 255, 255, 180)  # gridlines
WHITE_GHOST = (255, 255, 255, 135)  # the orbit's far side, passing behind

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def load_font(size: int):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _arc_point(box, deg):
    """Point on the ellipse inscribed in `box` at Pillow's arc angle `deg`."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    rad = math.radians(deg)
    return (cx + rx * math.cos(rad), cy + ry * math.sin(rad))


def _arrowhead(draw, box, deg, length, spread, fill, flip=False):
    """Triangle at the ellipse point `deg`, aligned with the arc's tangent."""
    tip = _arc_point(box, deg)
    # Tangent direction from a small step along the arc.
    ahead = _arc_point(box, deg + (-4 if flip else 4))
    ang = math.atan2(ahead[1] - tip[1], ahead[0] - tip[0])
    left = (tip[0] - length * math.cos(ang - spread),
            tip[1] - length * math.sin(ang - spread))
    right = (tip[0] - length * math.cos(ang + spread),
             tip[1] - length * math.sin(ang + spread))
    draw.polygon([tip, left, right], fill=fill)


def render(size: int, tile: bool = True, ss: int = 4) -> Image.Image:
    """The artwork at `size` px. `tile=False` drops the rounded square."""
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if tile:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S // 6, fill=TEAL)

    cx, cy = S * 0.5, S * 0.44          # sphere sits above the wordmark
    R = S * 0.26                        # sphere radius
    stroke = max(ss, round(S * 0.016))
    grid = max(ss, round(S * 0.010))

    sphere_box = [cx - R, cy - R, cx + R, cy + R]

    # Orbit ring: wide, shallow ellipse through the sphere's equator. The far
    # (top) half is drawn first and dimmer — it passes BEHIND the sphere; the
    # near (bottom) half comes last, solid, with the arrowhead. That front/
    # back split is what makes it read as rotation around a solid object.
    orx, ory = S * 0.42, S * 0.125
    orbit_box = [cx - orx, cy - ory, cx + orx, cy + ory]
    orbit_w = max(ss, round(S * 0.018))
    d.arc(orbit_box, start=192, end=348, fill=WHITE_GHOST, width=orbit_w)

    # Sphere body + rim.
    d.ellipse(sphere_box, fill=TEAL_DEEP, outline=WHITE, width=stroke)

    # Gridlines, clipped to the sphere: equator + one parallel each side,
    # a straight prime meridian + one curved meridian each side.
    grid_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid_layer)
    for lat in (-0.52, 0.0, 0.52):                    # parallels
        y = cy + R * lat * 1.35
        half = math.sqrt(max(0.0, R * R - (y - cy) ** 2))
        ry = half * 0.24
        g.ellipse([cx - half, y - ry, cx + half, y + ry],
                  outline=WHITE_SOFT, width=grid)
    g.line([cx, cy - R, cx, cy + R], fill=WHITE_SOFT, width=grid)
    for rx_f in (0.45, 0.80):                         # meridians
        g.ellipse([cx - R * rx_f, cy - R, cx + R * rx_f, cy + R],
                  outline=WHITE_SOFT, width=grid)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse(
        [cx - R + stroke, cy - R + stroke, cx + R - stroke, cy + R - stroke],
        fill=255,
    )
    img.paste(grid_layer, (0, 0), Image.composite(
        grid_layer.getchannel("A"), Image.new("L", (S, S), 0), mask))
    d = ImageDraw.Draw(img)

    # Near half of the orbit, in front of the sphere, ending in an arrowhead.
    d.arc(orbit_box, start=22, end=158, fill=WHITE, width=orbit_w)
    _arrowhead(d, orbit_box, 20, length=S * 0.052, spread=0.52, fill=WHITE)

    # Wordmark under the sphere.
    text = "360°"
    font = load_font(int(S * 0.185))
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2 - bbox[0], S * 0.70), text, font=font, fill=WHITE)

    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="assets/icon-art.png")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--favicons", action="store_true",
                    help="also regenerate assets/favicon/*.png at their sizes")
    args = ap.parse_args()

    art = render(args.size)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    art.save(args.out)
    print(f"[icon] wrote {args.out} ({args.size}x{args.size})")

    if args.favicons:
        for size, name in [(16, "favicon-16x16.png"), (32, "favicon-32x32.png"),
                           (96, "favicon-96x96.png"),
                           (180, "apple-touch-icon.png"),
                           (192, "android-chrome-192x192.png"),
                           (512, "android-chrome-512x512.png")]:
            render(size).save(f"assets/favicon/{name}")
            print(f"[icon] wrote assets/favicon/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
