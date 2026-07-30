# ── stage 1: generate the static site from data/planets.json ──
# The data file is NOT in git (a 6k-planet build is ~90 MB): it lives in a GitHub
# Release named by data/RELEASE. Local builds that have the file on disk use it as-is;
# clean builds (Dokploy cloning the repo) download it. Pass GH_TOKEN if the repo is
# private (build arg on Dokploy: GH_TOKEN=<fine-grained read token>).
FROM python:3.11-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# Preflight: fail in seconds if the build disk can't fit this deploy, instead of
# discovering it at the final COPY after the ~100 s render. The site output exists TWICE
# while the image assembles (build stage + final image), on top of the still-running
# previous image, plus the ~90 MB dataset — so demand headroom above the raw size.
# The output is ~0.56 GB since the sky-chart starfield became one shared file (it was
# ~4.5 GB when this gate was written, which is why the floor used to be 12 GB — that
# would now fail deploys on hosts with plenty of room); ~165 MB of it is the per-planet
# Open Graph share cards. Override: MIN_FREE_GB=<n>.
ARG MIN_FREE_GB=4
RUN free_kb=$(df -Pk / | awk 'NR==2 {print $4}'); \
    need_kb=$((MIN_FREE_GB * 1024 * 1024)); \
    if [ "$free_kb" -lt "$need_kb" ]; then \
      echo "ERROR: $((free_kb / 1024 / 1024)) GB free on the build disk, ~${MIN_FREE_GB} GB needed" >&2; \
      echo "(site output is ~0.56 GB, copied between stages; old images/cache eat the rest)." >&2; \
      echo "Free space on the host first: docker image prune -af && docker builder prune -af" >&2; \
      exit 1; \
    fi; \
    echo "preflight: $((free_kb / 1024 / 1024)) GB free, need ${MIN_FREE_GB} GB - ok"

# Install deps first for layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY pipeline ./pipeline
RUN uv sync --frozen --no-dev

# Copy the rest (templates, static, data) and render.
COPY . .
ARG GH_TOKEN=""
# The canonical origin, e.g. https://exoplanetpalette.com. Open Graph needs absolute URLs
# and a sitemap of relative paths is invalid, so without this the build still emits share
# tags (root-relative) but writes no sitemap.xml. Set it as a build arg on the deploy host.
ARG SITE_BASE_URL=""
# Visitor analytics. The PostHog *project* token (phc_…, public and write-only — it ships in
# the page by design). Left empty, the build emits no analytics code at all, which is what
# every local and preview build wants. Set it as a build arg on the deploy host only.
ARG POSTHOG_KEY=""
# Fetch the dataset, render, then delete the dataset — all in ONE layer. Split into
# separate RUNs, the ~90 MB planets.json would be baked into a cached layer on every
# deploy host forever; fetched and removed inside the same step, it never persists
# anywhere once the site is rendered.
RUN GH_TOKEN="$GH_TOKEN" uv run python scripts/fetch_data.py \
    && SITE_BASE_URL="$SITE_BASE_URL" POSTHOG_KEY="$POSTHOG_KEY" \
       uv run python -m web.build --out /dist \
    && rm -f data/planets.json

# ── stage 2: serve the static output with nginx ──
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /dist /usr/share/nginx/html
EXPOSE 80
