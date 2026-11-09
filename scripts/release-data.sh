#!/usr/bin/env bash
# Publish data/planets.json as a GitHub Release asset and point data/RELEASE at it.
#
# The repo is code-only (planets.json is gitignored — a 6k build is ~90 MB); releases
# carry the data. Deploy builds fetch the asset via scripts/fetch_data.py using the tag
# committed in data/RELEASE.
#
# Usage:  scripts/release-data.sh [tag]        (default tag: data-YYYYMMDD-HHMM)
# After it succeeds: commit data/RELEASE and push — the deploy webhook does the rest.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

DATA=data/planets.json
[ -f "$DATA" ] || { echo "error: $DATA not found — run the pipeline first" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "error: gh not authenticated — run: gh auth login" >&2; exit 1; }

TAG="${1:-data-$(date +%Y%m%d-%H%M)}"

N=$(python3 -c "import json;d=json.load(open('$DATA'));print(len(d['planets']))")
SCHEMA=$(python3 -c "import json;print(json.load(open('$DATA'))['schema_version'])")
SIZE=$(python3 -c "import os;print(f'{os.path.getsize(\"$DATA\")/1e6:.1f}')")
# The two values that actually identify this build — the schema version identifies neither the
# code nor the upstream data.
SNAPSHOT=$(python3 -c "import json;p=json.load(open('$DATA')).get('provenance',{});print(p.get('upstream',{}).get('snapshot_at') or 'unknown')")
COMMIT=$(python3 -c "import json;p=json.load(open('$DATA')).get('provenance',{});print(p.get('code',{}).get('short') or 'unknown')")

# Reuse the build's input snapshot; publishing must never acknowledge newer Archive data.
MANIFEST=data/manifest.json
echo "Writing $MANIFEST from the saved build inputs..."
uv run python -m pipeline drift --emit-manifest "$MANIFEST" --planets "$DATA"

# Validate the snapshot before modifying the artifact's release identity.
python3 scripts/stamp_release_tag.py "$DATA" "$TAG"

gh release create "$TAG" "$DATA" "$MANIFEST" \
  --title "Planet data $TAG" \
  --notes "planets.json: $N planets, schema v$SCHEMA, $SIZE MB. Built at commit \`$COMMIT\` from an Exoplanet Archive snapshot of $SNAPSHOT — \`pscomppars\` is a live table, so that timestamp, not the schema version, is what makes two releases comparable. The same values travel inside the file, under \`provenance\`. Consumed by the deploy build via scripts/fetch_data.py. manifest.json records the Archive fingerprint this was built from and is the drift probe's baseline."

echo "$TAG" > data/RELEASE
echo
echo "Release $TAG published ($N planets, $SIZE MB)."
echo "Next: git add data/RELEASE && git commit -m 'Data release $TAG' && push — the deploy rebuilds from it."
