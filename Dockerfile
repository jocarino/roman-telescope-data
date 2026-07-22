# ── stage 1: generate the static site from the committed data/planets.json ──
FROM python:3.11-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# Install deps first for layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY pipeline ./pipeline
RUN uv sync --frozen --no-dev

# Copy the rest (templates, static, data) and render.
COPY . .
RUN uv run python -m web.build --out /dist

# ── stage 2: serve the static output with nginx ──
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /dist /usr/share/nginx/html
EXPOSE 80
