"""Prepare the solar-system surface maps shipped in web/static/tex/.

Downloads the public equirectangular maps for the five anchors, downsamples them to a
web-sized 1024x512, and prints each map's mean colour. That mean is what the renderer
divides by: the shader multiplies every texel by (derived colour / map mean), so the
rescaled map's own average is exactly the planet's physics-derived hex. Paste the printed
values into web/textures.py.

The mean is taken in the SAME (sRGB-encoded, gamma) space the shader works in, weighted by
cos(latitude) so the stretched polar rows of an equirectangular map don't outvote the
equator. Run:  python3 tools/prep_textures.py --out web/static/tex
"""

from __future__ import annotations

import argparse
import math
import urllib.request
from pathlib import Path

from PIL import Image

# id -> (source URL, longest side of the source we keep). Every one is a real map published
# for public use; credits live beside the metadata in web/textures.py.
SOURCES: dict[str, str] = {
    "earth": "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/"
    "world.topo.bathy.200412.3x5400x2700.jpg",  # composited with EARTH_CLOUDS below
    "jupiter": "https://www.solarsystemscope.com/textures/download/2k_jupiter.jpg",
    "saturn": "https://www.solarsystemscope.com/textures/download/2k_saturn.jpg",
    "uranus": "https://www.solarsystemscope.com/textures/download/2k_uranus.jpg",
    "neptune": "https://www.solarsystemscope.com/textures/download/2k_neptune.jpg",
}
RING_SRC = "https://www.solarsystemscope.com/textures/download/2k_saturn_ring_alpha.png"

# Blue Marble ships the surface and the clouds as separate layers, and the bare surface is the
# wrong map for us: our Earth colour comes from a measured whole-disc albedo, which is the
# albedo of a CLOUDY planet. Composited cloud-free, Earth's map averages far darker than that
# colour, and the rescale then has to multiply by ~4 — blowing the ice caps to white while the
# oceans stay black. With the clouds back on, the map's own average is close to the derived
# colour and the rescale is gentle, which is the honest state of affairs: Earth is bright
# because it is cloudy.
EARTH_CLOUDS = (
    "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud_combined_2048.jpg"
)

W, H = 1024, 512
QUALITY = 82


def _fetch(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "exoplanet-palette/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as f:
        f.write(r.read())
    return dest


def mean_rgb(img: Image.Image) -> tuple[float, float, float]:
    """cos(lat)-weighted mean of an equirectangular map, in 0-255 sRGB-encoded space."""
    px = img.convert("RGB").load()
    w, h = img.size
    tot = [0.0, 0.0, 0.0]
    wsum = 0.0
    for y in range(h):
        lat = (0.5 - (y + 0.5) / h) * math.pi  # +pi/2 (north) .. -pi/2 (south)
        wt = math.cos(lat)
        row = [0.0, 0.0, 0.0]
        for x in range(w):
            r, g, b = px[x, y]
            row[0] += r
            row[1] += g
            row[2] += b
        for i in range(3):
            tot[i] += (row[i] / w) * wt
        wsum += wt
    return tuple(t / wsum for t in tot)  # type: ignore[return-value]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="web/static/tex", type=Path)
    ap.add_argument("--cache", default=Path.home() / ".cache" / "exo-textures", type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)

    for pid, url in SOURCES.items():
        raw = _fetch(url, args.cache / f"{pid}{Path(url).suffix or '.jpg'}")
        img = Image.open(raw).convert("RGB").resize((W, H), Image.LANCZOS)
        if pid == "earth":
            clouds = Image.open(_fetch(EARTH_CLOUDS, args.cache / "earth-clouds.jpg"))
            mask = clouds.convert("L").resize((W, H), Image.LANCZOS)
            img = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), img, mask)
        dest = args.out / f"{pid}.jpg"
        img.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        r, g, b = mean_rgb(img)
        print(
            f'    "{pid}": mean=({r:.2f}, {g:.2f}, {b:.2f})  '
            f"-> #{round(r):02x}{round(g):02x}{round(b):02x}  "
            f"({dest.stat().st_size // 1024} kB)"
        )

    # Saturn's rings: a 1-D radial strip (colour + opacity), kept as PNG for the alpha.
    raw = _fetch(RING_SRC, args.cache / "saturn_ring.png")
    ring = Image.open(raw).convert("RGBA").resize((1024, 1), Image.LANCZOS)
    rdest = args.out / "saturn-ring.png"
    ring.save(rdest, "PNG", optimize=True)
    print(f"    ring -> {rdest} ({rdest.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
