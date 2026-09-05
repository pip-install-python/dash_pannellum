"""Cache lifetimes for the static files this app serves (1.6.44 item 6g).

MEASURED ON THIS HOST'S WIRE BEFORE PORTING, 2026-09-05, and the reading
differs from the drop's in a way worth recording: the rider says
``/assets/main.css`` is ``cache-control: no-cache`` fleet-wide. Here it
carries **no ``cache-control`` header at all** —

    HTTP/2 200
    content-type: text/css; charset=utf-8
    cf-cache-status: DYNAMIC

Same practical outcome, different cause. `no-cache` is an instruction to
revalidate; nothing at all leaves the edge to apply its own default, and
Cloudflare's default for an un-headered origin response is not to store it.
Either way `cf-cache-status: DYNAMIC` says the edge stored nothing and the
origin answered every request for the stylesheet.

Only ``/assets/`` is given a lifetime here, and deliberately:

* Dash's own ``/_dash-component-suites/`` URLs are fingerprinted and the
  package already sets a long immutable lifetime on them — a second opinion
  from this app could only make that worse;
* documents must keep revalidating. A page, ``/llms.txt``, ``/healthz`` and
  anything under ``/admin`` or ``/api`` are answers about right now, and one
  hour of a stale one is a bug report nobody can reproduce.

THE PAYOFF IS LARGER HERE THAN ON THE TEMPLATE, because of what this fork
is. ``assets/`` is 5.3 MB, and 4.9 MB of that is ``assets/tilesets/`` — the
panorama tiles the documented component loads to render a 360° view. Those
are immutable image tiles fetched many-per-page, and until now every one of
them was revalidated against the origin on every page load. The CSS and JS
that the template's version of this file was about are 52 KB of the total.

The window is one hour with a day of ``stale-while-revalidate``: assets here
are NOT fingerprinted (``main.css`` keeps its name across deploys), so the
lifetime is the longest a CSS fix may take to reach a returning reader.
"""
from __future__ import annotations

ASSET_PREFIX = "/assets/"
ASSET_CACHE_CONTROL = "public, max-age=3600, stale-while-revalidate=86400"


def cache_control_for(path: str) -> str | None:
    """The ``Cache-Control`` this app wants on ``path``, or None to leave it.

    None is the answer for everything that is not an unfingerprinted static
    asset — the caller must not invent a header for a document.
    """
    return ASSET_CACHE_CONTROL if (path or "").startswith(ASSET_PREFIX) else None
