#!/usr/bin/env python3
"""Write the release tag into `planets.json`'s provenance header, so the published file
knows its own name.

The tag is chosen at publish time, after the build has already run, so the pipeline cannot
know it. Without this step `provenance.release_tag` stays null and a downloaded file can be
matched to its release only by whoever still has the URL it came from.

Called by scripts/release-data.sh before `gh release create`; it rewrites the local file in
place so the copy on disk and the copy uploaded are the same bytes.

Usage:  python3 scripts/stamp_release_tag.py data/planets.json data-20260805-1200
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def stamp(path: Path, tag: str) -> None:
    doc = json.loads(path.read_text())
    prov = doc.get("provenance")
    if not isinstance(prov, dict):
        raise SystemExit(
            f"{path} has no provenance header — it was built by a pipeline older than "
            "2026-08-05. Rebuild before releasing, or the published file will not say what "
            "it was built from."
        )
    prov["release_tag"] = tag
    # indent=2 to match pipeline/emit/writer.py, so re-stamping is a one-line diff.
    path.write_text(json.dumps(doc, indent=2))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    stamp(Path(argv[1]), argv[2])
    print(f"Stamped release_tag={argv[2]} into {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
