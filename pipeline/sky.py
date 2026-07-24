"""Sky position: where the host star sits in Earth's sky, and whether you could see it.

Constellation determination follows Roman (1987, PASP 99, 695): the IAU constellation
boundaries (CDS catalogue VI/42, embedded in `pipeline/data/constellation_boundaries.dat`)
are declination strips in B1875.0 coordinates, so we precess the J2000 position back to
B1875 with the IAU 1976 precession angles (Meeus, *Astronomical Algorithms*, ch. 21) and
scan the table. Accuracy is arcsecond-level — far tighter than the arcminute scale of the
boundary corners — and needs no astropy dependency.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from pipeline.models import SkyPosition

_BOUNDARIES_FILE = Path(__file__).parent / "data" / "constellation_boundaries.dat"

# Conventional dark-sky naked-eye limit. Suburban skies cut off nearer V ~ 5, so the UI
# wording must say "under a dark sky", never promise visibility from a city.
NAKED_EYE_LIMIT_VMAG = 6.5

# Julian centuries from J2000.0 to B1875.0 (the boundary table's epoch).
# JD(B1875.0) = 2415020.31352 - 25 * 365.242198781 = 2405889.258535
_T_B1875 = (2405889.258535 - 2451545.0) / 36525.0

# The 88 IAU constellations: abbreviation -> full (nominative) name.
CONSTELLATION_NAMES: dict[str, str] = {
    "And": "Andromeda",
    "Ant": "Antlia",
    "Aps": "Apus",
    "Aql": "Aquila",
    "Aqr": "Aquarius",
    "Ara": "Ara",
    "Ari": "Aries",
    "Aur": "Auriga",
    "Boo": "Boötes",
    "Cae": "Caelum",
    "Cam": "Camelopardalis",
    "Cap": "Capricornus",
    "Car": "Carina",
    "Cas": "Cassiopeia",
    "Cen": "Centaurus",
    "Cep": "Cepheus",
    "Cet": "Cetus",
    "Cha": "Chamaeleon",
    "Cir": "Circinus",
    "CMa": "Canis Major",
    "CMi": "Canis Minor",
    "Cnc": "Cancer",
    "Col": "Columba",
    "Com": "Coma Berenices",
    "CrA": "Corona Australis",
    "CrB": "Corona Borealis",
    "Crt": "Crater",
    "Cru": "Crux",
    "Crv": "Corvus",
    "CVn": "Canes Venatici",
    "Cyg": "Cygnus",
    "Del": "Delphinus",
    "Dor": "Dorado",
    "Dra": "Draco",
    "Equ": "Equuleus",
    "Eri": "Eridanus",
    "For": "Fornax",
    "Gem": "Gemini",
    "Gru": "Grus",
    "Her": "Hercules",
    "Hor": "Horologium",
    "Hya": "Hydra",
    "Hyi": "Hydrus",
    "Ind": "Indus",
    "Lac": "Lacerta",
    "Leo": "Leo",
    "Lep": "Lepus",
    "Lib": "Libra",
    "LMi": "Leo Minor",
    "Lup": "Lupus",
    "Lyn": "Lynx",
    "Lyr": "Lyra",
    "Men": "Mensa",
    "Mic": "Microscopium",
    "Mon": "Monoceros",
    "Mus": "Musca",
    "Nor": "Norma",
    "Oct": "Octans",
    "Oph": "Ophiuchus",
    "Ori": "Orion",
    "Pav": "Pavo",
    "Peg": "Pegasus",
    "Per": "Perseus",
    "Phe": "Phoenix",
    "Pic": "Pictor",
    "PsA": "Piscis Austrinus",
    "Psc": "Pisces",
    "Pup": "Puppis",
    "Pyx": "Pyxis",
    "Ret": "Reticulum",
    "Scl": "Sculptor",
    "Sco": "Scorpius",
    "Sct": "Scutum",
    "Ser": "Serpens",
    "Sex": "Sextans",
    "Sge": "Sagitta",
    "Sgr": "Sagittarius",
    "Tau": "Taurus",
    "Tel": "Telescopium",
    "TrA": "Triangulum Australe",
    "Tri": "Triangulum",
    "Tuc": "Tucana",
    "UMa": "Ursa Major",
    "UMi": "Ursa Minor",
    "Vel": "Vela",
    "Vir": "Virgo",
    "Vol": "Volans",
    "Vul": "Vulpecula",
}


@lru_cache(maxsize=1)
def _boundaries() -> tuple[tuple[float, float, float, str], ...]:
    rows: list[tuple[float, float, float, str]] = []
    for line in _BOUNDARIES_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ra_lo, ra_hi, dec_lo, abbr = line.split()
        rows.append((float(ra_lo), float(ra_hi), float(dec_lo), abbr))
    return tuple(rows)


def _precess_j2000_to_b1875(ra_deg: float, dec_deg: float) -> tuple[float, float]:
    """IAU 1976 precession of a J2000.0 position to B1875.0, in degrees."""
    t = _T_B1875
    zeta = (2306.2181 * t + 0.30188 * t**2 + 0.017998 * t**3) / 3600.0
    z = (2306.2181 * t + 1.09468 * t**2 + 0.018203 * t**3) / 3600.0
    theta = math.radians((2004.3109 * t - 0.42665 * t**2 - 0.041833 * t**3) / 3600.0)
    a = math.radians(ra_deg + zeta)
    d = math.radians(dec_deg)
    big_a = math.cos(d) * math.sin(a)
    big_b = math.cos(theta) * math.cos(d) * math.cos(a) - math.sin(theta) * math.sin(d)
    big_c = math.sin(theta) * math.cos(d) * math.cos(a) + math.cos(theta) * math.sin(d)
    ra_out = (math.degrees(math.atan2(big_a, big_b)) + z) % 360.0
    return ra_out, math.degrees(math.asin(big_c))


def constellation_abbr(ra_deg: float, dec_deg: float) -> str:
    """IAU constellation abbreviation for a J2000 position (Roman 1987 table scan)."""
    ra_b, dec_b = _precess_j2000_to_b1875(ra_deg, dec_deg)
    ra_h = ra_b / 15.0
    for ra_lo, ra_hi, dec_lo, abbr in _boundaries():
        if dec_b >= dec_lo and ra_lo <= ra_h < ra_hi:
            return abbr
    return "Oct"  # unreachable: the table's last row spans the whole south pole


def format_ra(ra_deg: float) -> str:
    """RA in the astronomer-friendly form '22h 57m'."""
    total_h = (ra_deg % 360.0) / 15.0
    h = int(total_h)
    m = round((total_h - h) * 60.0)
    if m == 60:
        h, m = (h + 1) % 24, 0
    return f"{h}h {m:02d}m"


def format_dec(dec_deg: float) -> str:
    """Declination as '+20° 46′'."""
    sign = "−" if dec_deg < 0 else "+"
    mag = abs(dec_deg)
    d = int(mag)
    m = round((mag - d) * 60.0)
    if m == 60:
        d, m = d + 1, 0
    return f"{sign}{d}° {m:02d}′"


def build_sky(ra_deg: float, dec_deg: float, v_mag: float | None) -> SkyPosition:
    abbr = constellation_abbr(ra_deg, dec_deg)
    return SkyPosition(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        constellation=CONSTELLATION_NAMES.get(abbr, abbr),
        constellation_abbr=abbr,
        v_mag=v_mag,
        naked_eye=v_mag is not None and v_mag <= NAKED_EYE_LIMIT_VMAG,
    )
