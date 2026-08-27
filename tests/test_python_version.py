"""One fleet Python — image, matrix and render.yaml must agree.

Found by the ops seat reading the tree, not a report (2026-08-25): a repo can
declare three different Pythons at once — a patch-pinned Dockerfile, a matrix
one minor behind it, a render.yaml one behind that — and no battery can see
any of the disagreements, because nothing on the wire contradicts a
declaration. These pins hold every encoding to ONE minor, sourced from the
Dockerfile's FROM tag; /healthz's `python` field plus the
`python_matches_declared` battery check (scripts/network_smoke.py) hold the
serving host to the same one.

This repo's own instance of the defect, and why the file lands here
(2026-08-26): dependabot PR #1 moved the image to python:3.14-slim and was
merged, while ci.yml's matrix main still said 3.12 — so from that merge until
this commit the unit suite never once ran on the interpreter that serves
production. The docker job's boot and battery did run on 3.14, which is why
nothing was red; that is exactly the invisible half this file closes.

What is deliberately NOT here: no comparison of the RUNNING interpreter to the
fleet minor — the suite legitimately runs on the adjacent window legs (the
matrix's 3.13/3.12 rows), where that assertion would be false by design.
Image-vs-declaration is the battery's job, against a host.

TWO Pythons live in this repo's CI, and this file pins exactly one of them
(spec item 5, 1.6.28). This fork is a COMPONENT as well as a site:

  * SITE lane — .github/workflows/ci.yml and cd.yml. They install
    requirements.txt, boot the docs app, build the image and probe the live
    host. Held to the image's minor by everything below.
  * PACKAGE lane — .github/workflows/release.yml, which verifies the tag and
    builds the dash-pannellum wheel for PyPI. Its interpreter is the
    package's business: the wheel is pure-Python and its audience is every
    Dash user's environment, not this container. It is NOT scanned here, and
    a future sync must not "align" it — pinning a publish job to a container
    base is how the two Pythons get conflated.

Session-class for forks, not block cargo: it presumes a Dockerfile and a
render.yaml, which not every fork carries.
"""
from __future__ import annotations

import re

from conftest import REPO_ROOT

# The SITE lane, named once so the scope is impossible to widen by accident.
# release.yml is the package lane and is deliberately absent — see the module
# docstring.
SITE_WORKFLOWS = (".github/workflows/ci.yml", ".github/workflows/cd.yml")


def _fleet_minor() -> str:
    """The single source: the Dockerfile's FROM tag."""
    for line in (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines():
        m = re.match(r"FROM\s+python:(\S+)", line)
        if m:
            return m.group(1)
    raise AssertionError("Dockerfile has no `FROM python:` line")


def _uncommented(path) -> list[str]:
    return [
        ln for ln in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")
    ]


def _render_runtime() -> str:
    for ln in _uncommented("render.yaml"):
        m = re.match(r"\s*runtime:\s*(\S+)", ln)
        if m:
            return m.group(1)
    raise AssertionError("render.yaml declares no `runtime:`")


def test_dockerfile_tag_is_minor_only():
    """The patch pin IS the security bug: `3.11.8-slim` never receives a
    3.11.x fix release. The minor tag tracks them through Docker Hub."""
    tag = _fleet_minor()
    assert re.fullmatch(r"\d+\.\d+-slim", tag), (
        f"Dockerfile FROM tag is {tag!r} — must be a MINOR tag "
        "(python:X.Y-slim), never a patch pin"
    )


def test_render_yaml_agrees_with_the_image():
    """BRANCHES on the service runtime (1.6.28).

    `runtime: python` — the native runtime reads PYTHON_VERSION and requires
    a full X.Y.Z (its encoding, not ours): the value is REQUIRED and its
    MINOR must be the fleet Python.

    `runtime: docker` — THIS host's branch. Nothing reads PYTHON_VERSION
    there; the image is the interpreter. The key must be ABSENT: a value
    would read like the platform's setting and could never be true — the
    item's own defect class arriving through the fix. The absence is load-
    bearing rather than incidental, which is why it is asserted rather than
    assumed; if this service ever moves to Render's native runtime, this
    test flips branches by itself and demands the pin.

    Anything else fails loudly: extend the branch deliberately, never by
    accident."""
    minor = _fleet_minor().removesuffix("-slim")
    runtime = _render_runtime()
    lines = _uncommented("render.yaml")
    value = None
    for i, ln in enumerate(lines):
        if re.match(r"\s*- key: PYTHON_VERSION$", ln):
            m = re.search(r'value:\s*"([^"]+)"', lines[i + 1])
            value = m and m.group(1)
            break
    if runtime == "docker":
        assert value is None, (
            f"render.yaml declares PYTHON_VERSION {value!r} on a docker "
            "runtime — nothing reads it there; a string that looks like "
            "the platform's setting and can never be true is the drift "
            "class this file exists to kill. Delete the key."
        )
        return
    assert runtime == "python", (
        f"render.yaml runtime is {runtime!r} — this test knows `python` "
        "and `docker`; extend the branch deliberately"
    )
    assert value, "render.yaml declares no PYTHON_VERSION"
    assert re.fullmatch(r"\d+\.\d+\.\d+", value), (
        f"PYTHON_VERSION {value!r} — Render requires full X.Y.Z"
    )
    assert value.startswith(minor + "."), (
        f"render.yaml PYTHON_VERSION {value} vs image python:{minor}-slim — "
        "the native-runtime lane and the image lane disagree"
    )


def test_ci_matrix_main_and_singleton_jobs_agree_with_the_image():
    """SITE-lane pins only (see the module docstring): ci.yml's matrix main
    and its literal-pinned jobs (lint, pip-audit), plus cd.yml's verify
    runner. release.yml's pins belong to the wheel and are out of scope."""
    minor = _fleet_minor().removesuffix("-slim")
    ci = _uncommented(".github/workflows/ci.yml")

    mains = [m.group(1) for ln in ci
             if (m := re.match(r'\s*python:\s*\["([\d.]+)"\]', ln))]
    assert mains == [minor], (
        f"ci.yml matrix main {mains} vs image python:{minor}-slim"
    )

    # lint and pip-audit run literal python-version pins; the test job's is
    # `${{ matrix.python }}` and is deliberately not a literal.
    literals = [m.group(1) for ln in ci
                if (m := re.match(r'\s*python-version:\s*"([\d.]+)"', ln))]
    assert literals and set(literals) == {minor}, (
        f"ci.yml singleton jobs pin {literals}, image is python:{minor}-slim"
    )

    cd = _uncommented(".github/workflows/cd.yml")
    cd_literals = [m.group(1) for ln in cd
                   if (m := re.match(r'\s*python-version:\s*"([\d.]+)"', ln))]
    assert cd_literals and set(cd_literals) == {minor}, (
        f"cd.yml verify job pins {cd_literals}, image is python:{minor}-slim"
    )


def test_matrix_legs_are_the_adjacent_minors():
    """The compat window stays three wide: the include legs on the default
    backend are X.Y-1 and X.Y-2 (or X.Y+1 once it exists). The dash-bottom
    rows pin their own python and fall inside the same window, so they are
    swept by the same assertion rather than exempted."""
    major, y = (int(p) for p in _fleet_minor().removesuffix("-slim").split("."))
    allowed = {f"{major}.{y}", f"{major}.{y - 1}", f"{major}.{y - 2}",
               f"{major}.{y + 1}"}
    ci = _uncommented(".github/workflows/ci.yml")
    legs = [m.group(1) for ln in ci
            if (m := re.match(r'\s*- python:\s*"([\d.]+)"', ln))]
    assert legs, "the matrix has no include legs — the window collapsed to one"
    outside = [leg for leg in legs if leg not in allowed]
    assert not outside, (
        f"matrix legs {outside} fall outside the three-wide window around "
        f"{major}.{y}"
    )


def test_the_package_lane_is_out_of_scope_on_purpose():
    """A guard on the SCOPE, not on a version.

    release.yml builds the dash-pannellum wheel; its Python is not this
    image's. Nothing above reads that file, and this test exists so the
    omission reads as deliberate to the next session rather than as a gap
    worth closing — the fleet has already had one fork conflate a package
    matrix with its site lane and pin a publish job to a container base.
    """
    release = REPO_ROOT / ".github/workflows/release.yml"
    assert release.exists(), (
        "release.yml is gone — if the wheel moved elsewhere, re-scope this "
        "file's SITE_WORKFLOWS note rather than deleting the distinction"
    )
    assert str(release).endswith("release.yml")
    assert all("release.yml" not in wf for wf in SITE_WORKFLOWS), (
        "release.yml has been pulled into the SITE lane — the package's "
        "interpreter is not the image's; see the module docstring"
    )
