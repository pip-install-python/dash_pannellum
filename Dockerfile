# dash-pannellum docs — production image (Render docker runtime).
#
# NO node toolchain: the dash_pannellum component bundle + generated Python
# wrappers are COMMITTED to git (dash_pannellum/*.min.js + *.py), so
# `pip install .` works without npm. TRADE-OFF: changes under src/lib require
# a local `npm run build` and committing the regenerated artifacts.
FROM python:3.12-slim

WORKDIR /app

# curl is only for the container HEALTHCHECK below.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Without this, NONE of the app's boot diagnostics reach the platform's log
# stream. Python block-buffers stdout when it is a pipe rather than a TTY,
# and gunicorn never flushes it — on email.2plot.dev this swallowed the exact
# "network bulletin: off" line that would have revealed an unwired feature.
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

# dash-clerk-auth is not on PyPI; requirements.txt installs it from ./vendor.
COPY vendor ./vendor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# markdown2dash pins gunicorn<22, conflicting with the CVE-driven gunicorn>=23
# in requirements.txt (CVE-2024-6827, CVE-2024-1135 — request smuggling). Its
# real dependencies are all in requirements.txt already, so it is installed
# alone, without letting pip see the spurious pin. CI asserts the resulting
# gunicorn version inside this image, which is what keeps the dodge honest.
RUN pip install --no-cache-dir --no-deps markdown2dash==0.1.2

# The component package itself.
COPY pyproject.toml MANIFEST.in README.md LICENSE ./
COPY dash_pannellum ./dash_pannellum
RUN pip install --no-cache-dir .

# The docs app — an EXPLICIT list, not `COPY . .`, and the rule is: a new
# top-level directory enters this list in the same commit that creates it.
# The llms pass shipped a green CI and a dead deploy because tests run from
# the working tree while the container only holds what is COPY'd; the
# container-boot CI job exists to catch exactly this.
COPY run.py ./
COPY templates ./templates
COPY assets ./assets
COPY components ./components
COPY docs ./docs
COPY lib ./lib
COPY pages ./pages
COPY scripts ./scripts

# The 2plot.ai hub's hourly sweep probes /healthz; give the container the
# same check so an unhealthy process is visible to the orchestrator too.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8561}/healthz || exit 1

# Render injects PORT and ignores EXPOSE; env vars come from render.yaml /
# the dashboard — NEVER bake .env.
EXPOSE 8561

# The worker class must match the backend: FastAPI's server object is ASGI
# (uvicorn worker), Flask's is WSGI (gunicorn's default sync worker). One
# CMD serving both through the uvicorn worker is a trap — uvicorn wraps a
# WSGI app as ASGI2 and every request 500s with
# "Flask.__call__() missing 1 required positional argument".
CMD ["sh", "-c", "\
  if [ \"${DASH_BACKEND:-flask}\" = 'flask' ]; then WORKER_ARGS=''; \
  else WORKER_ARGS='-k uvicorn.workers.UvicornWorker'; fi; \
  exec gunicorn run:server $WORKER_ARGS --bind 0.0.0.0:${PORT:-8561} --workers ${WEB_WORKERS:-1} --timeout 120"]
