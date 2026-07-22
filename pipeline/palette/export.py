"""Palette export helpers. `.ase` (Adobe Swatch Exchange) is a small binary format that
imports directly into Photoshop / Illustrator / Affinity, so a designer can drop a planet's
palette straight into a document.
"""

from __future__ import annotations

import struct


def _hex_to_rgb01(hexcode: str) -> tuple[float, float, float]:
    h = hexcode.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _color_block(name: str, hexcode: str) -> bytes:
    r, g, b = _hex_to_rgb01(hexcode)
    name_utf16 = name.encode("utf-16-be") + b"\x00\x00"  # null-terminated UTF-16BE
    name_len = len(name_utf16) // 2  # in UTF-16 code units, incl. the null
    body = (
        struct.pack(">H", name_len)
        + name_utf16
        + b"RGB "
        + struct.pack(">fff", r, g, b)
        + struct.pack(">H", 2)  # colour type: 2 = normal
    )
    return struct.pack(">H", 0x0001) + struct.pack(">I", len(body)) + body


def ase_bytes(entries: list[tuple[str, str]]) -> bytes:
    """Build an .ase file from (name, hex) entries."""
    blocks = b"".join(_color_block(name, hexcode) for name, hexcode in entries)
    header = b"ASEF" + struct.pack(">HH", 1, 0) + struct.pack(">I", len(entries))
    return header + blocks
