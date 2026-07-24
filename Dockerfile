# ── stage 1: generate the static site from data/planets.json ──
# The data file is NOT in git (a 6k-planet build is ~90 MB): it lives in a GitHub
# Release named by data/RELEASE. Local builds that have the file on disk use it as-is;
# clean builds (Dokploy cloning the repo) download it. Pass GH_TOKEN if the repo is
# private (build arg on Dokploy: GH_TOKEN=<fine-grained read token>).
FROM python:3.11-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# Install deps first for layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY pipeline ./pipeline
RUN uv sync --frozen --no-dev

# Copy the rest (templates, static, data) and render.
COPY . .
ARG GH_TOKEN=""
RUN GH_TOKEN="$GH_TOKEN" uv run python scripts/fetch_data.py
RUN uv run python -m web.build --out /dist

# ── stage 2: serve the static output with nginx ──
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /dist /usr/share/nginx/html
EXPOSE 80
