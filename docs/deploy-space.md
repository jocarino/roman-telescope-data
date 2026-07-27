# Deploy disk space

A failed deploy with `no space left on device` at the final `COPY --from=build` step
(after the ~100 s site render succeeded) means the Docker host ran out of disk mid-build.
This page explains the space profile and the guardrails in place.

## Why deploys are disk-hungry

- `dist/` is **~4.2 GB**: 5,764 planet pages at ~770 KB each (plus the small
  long-press peek fragments). It was ~8.5 GB until the dead per-planet detail
  fragments — a full second copy of every page, for an htmx drawer that no longer
  exists — were dropped from the build. `du -sh dist/*/` to re-measure.
- During the image build that output exists **twice** — once in the build stage, once in
  the final nginx image — while the previous deploy's image is still present and running.
- Deploy hosts also accumulate **build cache and old images**: every deploy leaves layers
  behind until something prunes them.

Rule of thumb: a deploy transiently needs **~2× the site size plus headroom ≈ 12 GB** free.

## Guardrails in the Dockerfile

1. **Preflight check (first build step).** Fails in seconds with a clear message if the
   build disk has less than `MIN_FREE_GB` (default 12) free — instead of wasting the full
   render and dying at the copy. Tune per host with a build arg: `MIN_FREE_GB=<n>`.
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

## Possible next cut

The remaining bulk is the planet pages themselves (~770 KB each, dominated by the two
inline SVG spectra and the per-phase colour tables). Precompressing the output and
serving it with nginx's `gzip_static` would cut transfer size (not image size); moving
the spectra to fetched assets would cut both. Neither is done — the site fits again
after the fragment cut, so this is a note for the next time it doesn't.
