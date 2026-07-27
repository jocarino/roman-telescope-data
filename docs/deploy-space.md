# Deploy disk space

A failed deploy with `no space left on device` at the final `COPY --from=build` step
(after the ~100 s site render succeeded) means the Docker host ran out of disk mid-build.
This page explains the space profile and the guardrails in place.

## Why deploys are disk-hungry

- `dist/` is **~8.5 GB**: 5,764 planet pages at ~770 KB each, and `dist/fragments/`
  duplicates nearly all of it (the htmx drawer fragment is a second copy of each page
  body; `fragments/peek` is small). `du -sh dist/*/` to re-measure.
- During the image build that output exists **twice** — once in the build stage, once in
  the final nginx image — while the previous deploy's image is still present and running.
- Deploy hosts also accumulate **build cache and old images**: every deploy leaves layers
  behind until something prunes them.

Rule of thumb: a deploy transiently needs **~2× the site size plus headroom ≈ 20 GB** free.

## Guardrails in the Dockerfile

1. **Preflight check (first build step).** Fails in seconds with a clear message if the
   build disk has less than `MIN_FREE_GB` (default 20) free — instead of wasting the full
   render and dying at the copy. Tune per host with a build arg: `MIN_FREE_GB=15`.
2. **The dataset never persists.** `fetch_data.py` (≈90 MB planets.json), the site render,
   and `rm -f data/planets.json` run in **one** `RUN` layer, so the dataset is deleted the
   moment the site is rendered and is never baked into any cached layer.

## Host hygiene (Dokploy)

The repo can't prune the host; something on the host must. Either:

- enable Dokploy's scheduled **cluster/docker cleanup** (Settings → Cluster → Clean up),
  or
- cron the equivalent manually:

  ```sh
  docker image prune -af          # old images from previous deploys
  docker builder prune -af        # BuildKit cache (the big one for this repo)
  ```

Check the current damage with `docker system df`.

## The real fix, when it's worth it

Most of the 8.5 GB is the `fragments/planet/*` duplication: the drawer fragment is the
same markup as the full page. Serving the drawer from the full page with an
`hx-select="#detail-body"` (and deleting the per-planet fragment output) would roughly
**halve** the site — one build change, one attribute change, no visual difference.
Gzipping at the nginx layer (`gzip_static` + precompressed output) would cut transfer
size too, though not image size. Neither is done yet; this note is the reminder.
