"""/terms and /privacy — the Legal section (1.6.44 item 15).

Two pages, one shape each: a SINGLE markdown string that is both what the
browser renders and what the machine lane is handed as `llms_doc`. That is
the whole point of the shape — a site whose privacy page says one thing to a
reader and another to a crawler has two privacy policies, and only one of
them was reviewed. On THIS repo that risk is not theoretical: the fleet trap
this host earned is about a props table that was present in one lane and
absent in the other for a fortnight.

The privacy text is GENERATED FROM THE MECHANISM, not from a template. Every
claim in it is a claim about code in this repository, and
`tests/test_legal_pages.py` holds the two together by reading a REAL visit
row out of the tracker and asserting every key in it is described here. If
the tracker starts storing something the page does not mention, the test goes
red rather than the page going quietly false.

THIS FORK IS TWO THINGS and the Terms page has to say so. dash-pannellum is a
published PyPI package as well as this documentation site, and a reader
arriving at /terms is at least as likely to be asking about the component
they pip-installed as about the site. The template's Terms describes a
documentation template; this one describes a component and its docs.
"""
from __future__ import annotations

import dash_mantine_components as dmc
from markdown2dash import Admonition, Divider, Image, create_parser

from lib.constants import (
    BASE_URL,
    DISCORD_URL,
    GITHUB_URL,
    PUBLISHER,
    PYPI_URL,
    SITE_SHORT_NAME,
    UPSTREAM,
)
from lib.directives.headings import patch_renderer

TERMS_DESCRIPTION = (
    f"Terms of use for {SITE_SHORT_NAME}: what this site and the package it "
    "documents are, what they are not, and the terms both are offered under."
)
PRIVACY_DESCRIPTION = (
    f"What {SITE_SHORT_NAME} stores about a visit, what it does not store, "
    "and where the numbers go — described from the code that does it."
)


TERMS_DOC = f"""# Terms of Use

> {TERMS_DESCRIPTION}

## What this is

`{SITE_SHORT_NAME}` is two things, published by {PUBLISHER}:

- a **Python package** on PyPI — a Dash component wrapping the
  [{UPSTREAM["name"]}]({UPSTREAM["url"]}) WebGL panorama viewer;
- **this site**, which documents it.

Both are reference material. Nothing here is advice, neither is a service,
and nothing on this site is a commitment to keep any particular behaviour
working in your project.

## The package, the documentation, and the code in it

The prose and the code examples are published so you can read them, run them
and copy them. The package and this site are offered under the MIT licence,
stated in the repository, and that licence — not this page — is what governs
your use of the code:

- [{GITHUB_URL}]({GITHUB_URL})
- [{PYPI_URL}]({PYPI_URL})

The viewer this component wraps is a separate project with its own licence
and its own terms: [{UPSTREAM["name"]}]({UPSTREAM["url"]}). Panorama images,
tilesets and any other content you load into the viewer are yours, and
nothing here grants a licence to them or takes one from you.

Everything is offered **as is**, without warranty of any kind. Running a code
example, or shipping this component, against your own data and in your own
deployment is your decision and your responsibility.

## Accounts

Some pages are gated behind a sign-in. An account exists so the site can tell
whether you may see a page; it is not a subscription and carries no
entitlement. Accounts may be ended at any time, by you or by us, and the
[Privacy](/privacy) page describes what is kept while one exists.

## Links to other sites

This site links to other sites in the 2plot network and to third-party
projects. Those sites have their own terms and their own privacy practices,
and this page does not speak for them.

## Changes

These terms change when the site does. The change history for the whole
site and the package, including this page, is the
[Changelog](/changelog) and the repository's commit history — there is no
separate archive of previous versions, because the repository already is
one.

## Contact

Questions about these terms: the [Discord]({DISCORD_URL}) or an issue on
[the repository]({GITHUB_URL}).
"""


PRIVACY_DOC = f"""# Privacy

> {PRIVACY_DESCRIPTION}

This page describes what the code in this repository actually does. Each
claim below corresponds to something readable in
`lib/analytics_tracker.py`, and the test suite holds the two together.

**The package stores nothing.** If you installed `{SITE_SHORT_NAME}` from
PyPI and are using it in your own app, none of what follows applies to you —
the component renders a panorama in your visitor's browser and reports
nothing to anyone. This page is about *this website*.

## What is stored about a visit

Every request to this site that is not a bot or network machinery records one
row:

- the **time** of the request;
- the **path** requested;
- a **device type** (desktop, mobile, tablet, bot);
- the **User-Agent** string your browser or client sent;
- a **visitor key** — a keyed one-way hash of your network address and
  User-Agent, truncated, used to tell one visitor from another within the
  retention window;
- a **location**, if and only if the network edge in front of this site sent
  one (see below).

Crawler rows additionally carry the vendor identity the classifier
determined — which bot it was, and whether it verified.

## What is NOT stored

- **Your IP address.** It is read from the request so the site can tell one
  visitor from another, and then it is reduced to the visitor key and
  discarded. It is not written to disk. (An operator running their own copy
  of this site can set `ANALYTICS_KEEP_CLIENT_IP=1` to keep it. This site
  does not.)
- **Anything from a third-party lookup service.** Earlier versions of this
  site sent visitor addresses to a geolocation API. That code was removed —
  not disabled — in release 1.6.44. This app makes no outbound request about
  you.
- **Cookies for analytics.** The visitor key is computed per request from
  what your client already sent. Nothing is stored in your browser to track
  you. Signing in sets a session cookie, which is what keeps you signed in.

## Where location comes from

From the network edge, or not at all. Cloudflare sits in front of this site
and adds headers describing where a request entered its network:
`CF-IPCountry` always, and `CF-IPCity`, `CF-Region`, `CF-IPLatitude` and
`CF-IPLongitude` when the zone is configured to send them. Whatever arrives
is stored; whatever does not is simply absent. There is no lookup and no
fallback to one.

You can see which of those headers this host is actually receiving — they are
listed in the `geo.headers_seen` field of
[{BASE_URL}/healthz]({BASE_URL}/healthz).

## Network machinery is counted nowhere

The 2plot network's own traffic — health checks, deploy batteries, link
audits — carries a marker in its User-Agent and is dropped before anything is
recorded. It is not in these numbers, by design.

## How long it is kept, and where it goes

Rows are pruned on a retention window and the visit table is capped in size.
A daily summary — counts by day, by page, by country, by crawler vendor — is
sent to the 2plot network hub. The summary carries no visitor keys, no
addresses and no User-Agent strings: it is counts.

## Signing in

Sign-in is handled by Clerk. What Clerk stores about an account is governed
by Clerk's own privacy policy. This site keeps the identifier it needs to
decide what you may see.

## Questions

The [Discord]({DISCORD_URL}), or an issue on
[the repository]({GITHUB_URL}).
"""


def _render(markdown: str, page_id: str):
    """The docs renderer, so Legal shares one typography with everything else.

    `parse()` returns a LIST — splatting rather than nesting is not a style
    choice here: a list nested inside a children list renders the page EMPTY
    with a green suite (React #31, tests/test_layout_nesting.py).
    """
    parsed = (patch_renderer(),
              create_parser([Admonition(), Divider(), Image()])(markdown))[1]
    return dmc.Container(id=page_id, size="md", py="xl", children=parsed)
