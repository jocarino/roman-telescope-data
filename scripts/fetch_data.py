"""Fetch data/planets.json from the GitHub Release named in data/RELEASE.

The data file is too big to commit (a 6k-planet build is ~90 MB), so the repo is
code-only: each pipeline run's planets.json is uploaded as a release asset
(scripts/release-data.sh) and the deploy build downloads it here.

No-op when data/planets.json already exists (local checkouts have the real file on
disk). Public repos download via the browser URL; set GH_TOKEN for private repos
(the script then goes through the API asset endpoint). Stdlib only — runs in the
slim Docker build stage with no extra dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = os.environ.get("GH_REPO", "jocarino/roman-telescope-data")
DATA = Path("data/planets.json")
RELEASE_FILE = Path("data/RELEASE")


def _get(url: str, token: str | None, accept: str) -> bytes:
    req = urllib.request.Request(url, headers={"Accept": accept})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (github.com)
        return resp.read()


def main() -> None:
    if DATA.exists():
        print(f"{DATA} already present ({DATA.stat().st_size / 1e6:.1f} MB); nothing to fetch.")
        return
    if not RELEASE_FILE.exists():
        sys.exit(f"{RELEASE_FILE} missing: no data release tag to fetch from.")
    tag = RELEASE_FILE.read_text().strip()
    token = os.environ.get("GH_TOKEN") or None

    if token:
        # Private repo: resolve the asset id via the API, then download it.
        meta = json.loads(_get(
            f"https://api.github.com/repos/{REPO}/releases/tags/{tag}",
            token, "application/vnd.github+json",
        ))
        asset = next(a for a in meta["assets"] if a["name"] == DATA.name)
        blob = _get(asset["url"], token, "application/octet-stream")
    else:
        blob = _get(
            f"https://github.com/{REPO}/releases/download/{tag}/{DATA.name}",
            None, "application/octet-stream",
        )

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_bytes(blob)
    print(f"Fetched {DATA} from release {tag} ({len(blob) / 1e6:.1f} MB).")


if __name__ == "__main__":
    main()
