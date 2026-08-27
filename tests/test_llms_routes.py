"""The AI/LLM and SEO surfaces: llms.txt, sitemap.xml, robots.txt, canonicals."""

from __future__ import annotations

import json
import platform
import re
import xml.etree.ElementTree as ET

import pytest
from urllib.parse import urlparse

from conftest import BROWSER_ACCEPT, CRAWLER_UA
from lib import network_directory as nd
from lib.constants import BASE_URL

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def test_root_llms_txt_is_an_index(client):
    body = client.get("/llms.txt").text
    assert "# " in body, "llms.txt should open with a heading"
    assert "## Network" in body, "the cross-host directory is missing from llms.txt"


def test_every_page_has_its_own_llms_txt(client, page_paths):
    failures = []
    for path in page_paths:
        url = "/llms.txt" if path == "/" else f"{path.rstrip('/')}/llms.txt"
        response = client.get(url)
        if not response.ok or len(response.text) < 200:
            failures.append((url, response.status, len(response.text)))
    assert failures == [], f"per-page llms.txt missing or empty: {failures}"


def test_page_llms_txt_carries_the_page_prose(client):
    body = client.get("/components/tours/llms.txt").text
    assert "Virtual Tours" in body
    assert "hotspot" in body.lower(), "page prose did not reach /<page>/llms.txt"


def test_source_directives_are_expanded_in_llms_txt(client):
    """`.. source::` must inline the referenced file, not name it.

    The audience for /<page>/llms.txt is someone pasting it into a chat
    window; a directive reference is useless to them.
    """
    body = client.get("/components/tours/llms.txt").text
    assert ".. source::" not in body, "an unexpanded directive leaked into the prose"
    assert "from dash_pannellum import DashPannellum" in body, (
        "the referenced source file was not inlined"
    )


def test_robots_txt(client):
    body = client.get("/robots.txt").text
    assert "User-agent:" in body
    assert f"Sitemap: {BASE_URL}/sitemap.xml" in body, "robots.txt must point at this host's sitemap"


def test_robots_artifact_fingerprint(client):
    """The robots.txt crawler split is the network's proof-of-artifact.

    pip metadata is invisible from outside, so these exact robots.txt pairs
    are how a live host is fingerprinted as running the intended
    dash-improve-my-llms — the post-deploy check on every host in the
    rollout. If this fails locally, the installed package regressed.

    The signature, by release that introduced it:

    - 2.3.2: `OAI-SearchBot -> Allow` (ChatGPT search's crawler; pre-fix
      builds disallowed it).
    - 2.3.3: `ClaudeBot -> Disallow` (the actual *training* crawler, moved to
      the training bucket) while `Claude-User` and `Claude-SearchBot` — the
      user-triggered and search fetchers — are allowed.
    """
    lines = client.get("/robots.txt").text.splitlines()

    def rule(agent):
        idx = lines.index(f"User-agent: {agent}")
        return lines[idx + 1]

    assert rule("OAI-SearchBot") == "Allow: /", "pre-2.3.2 artifact"
    assert rule("ClaudeBot") == "Disallow: /", "pre-2.3.3 artifact"
    assert rule("Claude-User") == "Allow: /", "pre-2.3.3 artifact"
    assert rule("Claude-SearchBot") == "Allow: /", "pre-2.3.3 artifact"


def test_sitemap_lists_every_page_on_this_host(client, page_paths):
    body = client.get("/sitemap.xml").text
    root = ET.fromstring(body)
    locs = [el.text for el in root.findall(".//sm:url/sm:loc", SITEMAP_NS)]
    assert locs, "sitemap.xml contains no <url> entries"

    foreign = [loc for loc in locs if urlparse(loc).netloc != urlparse(BASE_URL).netloc]
    assert foreign == [], f"sitemap.xml lists URLs on another host: {foreign}"

    listed = {urlparse(loc).path.rstrip("/") or "/" for loc in locs}
    missing = {p.rstrip("/") or "/" for p in page_paths} - listed
    assert not missing, f"pages absent from sitemap.xml: {sorted(missing)}"


def test_canonical_points_at_this_host_and_path(client, page_paths):
    """The failure mode that deindexed a satellite for months.

    A canonical on the wrong host tells Google the page is a duplicate of
    somewhere else. Checked per page, because a template-level canonical is
    right on the home page and wrong everywhere else.
    """
    wrong = []
    for path in page_paths:
        html = client.get(path, user_agent=CRAWLER_UA).text
        found = re.findall(r'rel="canonical"\s+href="([^"]*)"', html)
        expected = f"{BASE_URL}{path}"
        if found != [expected]:
            wrong.append((path, found))
    assert wrong == [], f"bad canonical tags (expected exactly one, this host): {wrong}"


def test_exactly_one_canonical_tag_for_browsers(client):
    """A hard-coded canonical in index.html doesn't replace the injected one.

    It joins it, and two conflicting canonicals are read as no signal at all.

    Counts ELEMENTS, not the bare substring `rel="canonical"`. The template
    both explains itself in comments and now ships a script whose selector
    names the attribute (`link[rel="canonical"]`, the SPA URL sync) — neither
    is a canonical tag, and a substring count read both as one. Same lesson as
    the `dv-banner` chrome check below: match the markup, not the words, so a
    file may legitimately discuss what it is being checked for.
    """
    html = re.sub(r"<!--.*?-->", "", client.get("/getting-started").text, flags=re.S)
    tags = re.findall(r'<link[^>]+rel="canonical"[^>]*>', html)
    assert len(tags) == 1, f"expected exactly one canonical element, got {tags}"


def test_healthz(client):
    """The 2plot.ai hub probes this hourly on every backend.

    `app` must be the resolved reporting key — a wrong SATELLITE_APP_KEY
    overwrites another app's analytics rows on the hub, and this field is
    how the fleet battery catches it. `reporting` must be False here: the
    suite runs secretless, so the rollup thread has nothing to sign with.
    `python` is the serving interpreter (template 1.6.27 item 5) — asserted
    against the running one rather than a literal, because the suite
    legitimately runs on the matrix's window legs; holding the ARTIFACT to
    the image's minor is scripts/network_smoke.py's job, against a host.
    """
    response = client.get("/healthz")
    assert response.ok
    body = json.loads(response.text)
    assert body["ok"] is True
    assert body["app"] == "pannellum"
    assert body["reporting"] is False
    assert body["python"] == platform.python_version()


def test_healthz_is_live_not_a_snapshot(monkeypatch):
    """The payload must be built per request, not closed over at registration.

    This host carried the snapshot form until the round-3 sync: the route
    captured `health_payload(backend)` once and returned the same dict
    forever. Harmless while every field was static, and silently wrong the
    moment one is not — `geo` reports LIVE state and the route is registered
    long before any geo configuration runs, so a snapshot reports the
    guardrail unconfigured on a host where it is configured: the diagnostic
    lying in exactly the situation it exists for (found on llms-2plot-dev
    2026-08-23).
    """
    from types import SimpleNamespace

    from flask import Flask

    from lib.health import register_health_route

    monkeypatch.setenv("SATELLITE_APP_KEY", "before")
    stub = SimpleNamespace(server=Flask("healthz_snapshot_pin"))
    register_health_route(stub, "flask")
    probe = stub.server.test_client()
    assert probe.get("/healthz").get_json()["app"] == "before"

    monkeypatch.setenv("SATELLITE_APP_KEY", "after")
    assert probe.get("/healthz").get_json()["app"] == "after", (
        "the payload was captured at registration — a snapshot again"
    )

    # Flask lane: the route hands its OWN request headers to geo's
    # `resolved` — same contract the FastAPI test pins for Starlette.
    body = probe.get("/healthz", headers={"CF-IPCountry": "FR"}).get_json()
    if body.get("geo"):
        assert "FR" in body["geo"]["resolved"], body["geo"]


def test_healthz_identity_fields(monkeypatch):
    """`build` says which commit answered, `app` says which satellite.

    Different questions on a fleet where every host shares one template and
    a hostname can be repointed between services. `app` reads the env
    directly rather than satellite_reporter.app_key(), whose byte-copied
    fallback is "boilerplate" — a lie in the one field whose job is saying
    who answered. Unset must read "unknown", never another host's key.
    """
    from lib.health import health_payload

    monkeypatch.setenv("RENDER_GIT_COMMIT", "cafebabe")
    monkeypatch.setenv("SATELLITE_APP_KEY", "pannellum")
    payload = health_payload("flask")
    assert payload["build"] == "cafebabe"
    assert payload["app"] == "pannellum"

    monkeypatch.delenv("SATELLITE_APP_KEY")
    assert health_payload("flask")["app"] == "unknown", (
        "an unset key must not fall back to the template's directory key"
    )


def test_fastapi_healthz_renders_from_the_shared_payload(monkeypatch):
    """cd.yml's build-match wait polls /healthz for `build`.

    Pydantic DROPS keys HealthResponse does not declare, so a field added to
    the payload but not to the model is served on Flask and silently absent
    on FastAPI — which is how a FastAPI deploy fell into the "predates the
    build field" warning path forever, verifying whichever release happened
    to be serving (the muicharts defect, reintroduced per-backend; found on
    llms-2plot-dev 2026-08-23). This host RUNS FastAPI in production, so
    this is the lane the hub actually sweeps.
    """
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from lib.asgi_routes import build_health_router

    monkeypatch.setenv("RENDER_GIT_COMMIT", "cafebabe")
    monkeypatch.setenv("SATELLITE_APP_KEY", "pannellum")
    api = fastapi.FastAPI()
    api.include_router(build_health_router())
    body = TestClient(api).get(
        "/healthz", headers={"CF-IPCountry": "DE"}
    ).json()
    assert body["build"] == "cafebabe"
    assert body["app"] == "pannellum"
    assert body["backend"] == "fastapi"
    assert "reporting" in body, "this host's own field must survive the model"
    # Same trap, newest field: without `python` on HealthResponse the hub
    # sweeps this host forever and never learns which interpreter serves,
    # while the Flask lane publishes it and every local check passes. The
    # battery's python_matches_declared reads exactly this key.
    assert body.get("python") == platform.python_version(), (
        "the `python` field did not survive Pydantic — the fastapi lane is "
        "the one production serves and the hub sweeps"
    )
    # THIS request's headers must reach geo's `resolved`. The route passes
    # them explicitly because the Flask-context fallback can never see a
    # Starlette request — and this is the lane the hub sweeps in
    # production, where healthz answered "no request context" on every
    # sweep until template 1.6.12 (2026-08-23).
    if body.get("geo"):
        assert "DE" in body["geo"]["resolved"], body["geo"]


def test_resolved_country_reads_explicit_headers_without_a_request():
    """The context-free pin — the only one that can actually fail.

    The in-request pins above pass even if a Flask route drops its
    `headers=`: inside a request the context fallback reads the same
    headers, and the lanes that genuinely break (Starlette/Quart) are
    unreachable from a Flask-pinned suite. Calling _resolved_country
    with a plain dict OUTSIDE any request context has no fallback to
    hide behind (dash-flows' finding, 2026-08-23). This host is the one
    whose production proved the defect, so the pin that can fail belongs
    here more than anywhere.
    """
    from lib.health import _resolved_country

    result = _resolved_country({"CF-IPCountry": "DE"})
    if result.startswith("unavailable (pre-2.7.0"):
        pytest.skip("geo shipped in dash-improve-my-llms 2.7.0")
    assert "DE" in result, result


def test_healthz_geo_block_is_counts_not_codes():
    """Present on dash-improve-my-llms >= 2.7.0 (counts and flags only — a
    health endpoint is not where anyone learns policy), OMITTED on older
    packages rather than error-flagged: a host on an older floor is not
    broken, it predates the diagnostic. Its absence in PRODUCTION is the
    fleet's tell that the >=2.7.1 floor never reached the image."""
    from lib.health import health_payload

    payload = health_payload("flask")
    try:
        from dash_improve_my_llms import geo  # noqa: F401
    except ImportError:
        assert "geo" not in payload
    else:
        block = payload["geo"]
        assert isinstance(block["configured"], bool)
        assert isinstance(block["denied"], int), "counts, never country codes"
        assert not any(
            isinstance(v, (list, tuple)) for v in block.values()
        ), "the denylist's country codes must never reach this payload"


# ---------------------------------------------------------------------------
# Content negotiation on /<page>/llms.txt (dash-improve-my-llms 2.2.0)
#
# One URL, two audiences. Agents must get Markdown byte for byte; people who
# paste the URL into a browser get it rendered. The failure mode this guards
# against is subtle in both directions: viewer chrome leaking into the
# Markdown makes every agent in the network pay tokens for decoration and
# shows up in no dashboard, and a CDN that ignores `Vary` can hand a cached
# HTML response to the next agent that asks.
# ---------------------------------------------------------------------------

# A page whose prose never discusses the llms viewer itself, so any chrome
# markup found in its Markdown variant is genuinely leaked chrome.
PAGE_DOC = "/getting-started/llms.txt"

# Chrome is detected as rendered markup rather than as a bare class name. A
# Markdown document may legitimately discuss `dv-banner`; it can never contain
# `<div class="dv-banner">`. Keying on the token instead makes any page that
# writes about the viewer fail, which teaches people to stop writing about it.
CHROME = re.compile(r'<[a-z]+ class="dv-banner')


def test_agents_get_markdown(client):
    response = client.get(PAGE_DOC)
    assert response.ok
    assert "text/markdown" in response.content_type, response.content_type
    assert not CHROME.search(response.text), "viewer chrome leaked into the agent's copy"
    assert "<!DOCTYPE html>" not in response.text


def test_browsers_get_the_rendered_view(client):
    response = client.get(PAGE_DOC, accept=BROWSER_ACCEPT)
    assert response.ok
    assert "text/html" in response.content_type, response.content_type
    assert CHROME.search(response.text), "the viewer header is missing"
    assert "mk-wordmark" in response.text, "the network wordmark is missing"


def test_the_banner_renders_its_panels_without_a_bulletin(client):
    """Tips and What's new appear with the package's built-in defaults.

    `configure_bulletin()` is deliberately unwired here — 2plot.dev doesn't
    serve the endpoint yet — and this pins the fact that the header is fully
    formed regardless. Without it, "the banner looks wrong" could mean either
    a missing bulletin or a broken viewer, and those have very different
    fixes.
    """
    html = client.get(PAGE_DOC, accept=BROWSER_ACCEPT).text
    assert "Tips for getting started" in html
    assert "Append /llms.txt to any page URL" in html, "the default tip is missing"
    assert "What's new" in html
    assert "No announcements." in html, "the empty-state text is missing"


def test_the_banner_carries_this_app_and_network_identity(client):
    """The banner must name *this* site, not the package's demo app."""
    html = client.get(PAGE_DOC, accept=BROWSER_ACCEPT).text
    assert nd.NETWORK_NAME in html, "the banner does not name the network"
    assert nd.HUB_URL in html, "the banner does not link the hub"


# (The boilerplate keeps an extra test here pinning that a page may *discuss*
# `dv-banner` in prose without tripping the chrome check. No page on this site
# documents the viewer, so that distinction is pinned upstream instead.)


def test_crawlers_get_markdown_not_the_viewer(client):
    """Googlebot asks for HTML by habit. It still gets the document.

    The rendered view is `noindex` precisely so it never competes with the
    real page, so serving it to a crawler would waste the fetch.
    """
    response = client.get(PAGE_DOC, user_agent=CRAWLER_UA)
    assert "text/markdown" in response.content_type, response.content_type


def test_both_variants_send_vary_accept(client):
    """Without `Vary: Accept`, a shared cache serves whichever variant it saw
    first to everyone — including HTML to an agent."""
    for accept in (None, BROWSER_ACCEPT):
        response = client.get(PAGE_DOC, accept=accept)
        assert "accept" in response.header("Vary").lower(), (
            f"Vary is {response.header('Vary')!r} for Accept={accept!r}"
        )


def test_query_overrides_beat_the_accept_header(client):
    """`?raw=1` for a person debugging in a browser, `?format=html` for a
    person sharing a link from a terminal."""
    raw = client.get(f"{PAGE_DOC}?raw=1", accept=BROWSER_ACCEPT)
    assert "text/markdown" in raw.content_type, raw.content_type

    rendered = client.get(f"{PAGE_DOC}?format=html")
    assert "text/html" in rendered.content_type, rendered.content_type


def test_the_rendered_view_is_noindex(client):
    """It is the same content as the page it documents. Indexed, it would
    compete with it."""
    response = client.get(PAGE_DOC, accept=BROWSER_ACCEPT)
    assert re.search(r'<meta[^>]+name="robots"[^>]+noindex', response.text), (
        "the viewer must not be indexable"
    )


# ---------------------------------------------------------------------------
# The navigation block (2.2.0)
#
# A page's llms.txt is usually read in isolation — pasted into a chat, handed
# to an agent. Before 2.2.0 it was a dead end: it described one page and gave
# an agent nothing to follow.
# ---------------------------------------------------------------------------


def test_page_documents_are_not_dead_ends(client):
    body = client.get(PAGE_DOC).text
    assert f"{BASE_URL}/llms.txt" in body, "no route back to this site's index"
    assert f"{BASE_URL}/sitemap.xml" in body, "no sitemap link"


def test_nav_block_points_one_level_up_the_hub_chain(client):
    """A subdomain names its section hub, not the network root.

    Each llms.txt then has exactly one "up" link and an agent walks the chain.
    This app is a `*.2plot.dev` subdomain, so its hub is 2plot.dev.
    """
    body = client.get(PAGE_DOC).text
    assert f"{nd.HUB_URL}/llms.txt" in body, f"expected the hub chain to reach {nd.HUB_URL}"


def test_nav_block_is_absent_from_the_root_index(client):
    """The root document *is* the site index; pointing it at itself is noise."""
    body = client.get("/llms.txt").text
    assert "## Pages" in body, "the root document should be an index"
    assert not CHROME.search(body), "viewer chrome leaked into the root index"
