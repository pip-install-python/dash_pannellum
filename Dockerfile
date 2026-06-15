FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip

# Install python requirements (includes the vendored dash-improve-my-llms 2.0)
COPY requirements.txt .
COPY vendor ./vendor
RUN pip install -r requirements.txt

# Install the component package itself
COPY pyproject.toml MANIFEST.in README.md LICENSE ./
COPY dash_pannellum ./dash_pannellum
RUN pip install .

COPY . .

EXPOSE 8561

# DASH_BACKEND=fastapi (from .env / compose) serves ASGI; the uvicorn worker
# class handles both the FastAPI and Flask backends.
CMD ["gunicorn", "run:server", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8561"]
