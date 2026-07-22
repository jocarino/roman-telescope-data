"""The .ase palette exporter produces a well-formed Adobe Swatch Exchange file."""

from __future__ import annotations

import struct

from pipeline.palette.export import ase_bytes


def test_ase_header_and_block_count():
    data = ase_bytes([("Base", "#7ad3ff"), ("Shade", "#003d5c")])
    assert data[:4] == b"ASEF"
    major, minor = struct.unpack(">HH", data[4:8])
    assert (major, minor) == (1, 0)
    assert struct.unpack(">I", data[8:12])[0] == 2  # two colour blocks


def test_ase_first_block_is_rgb_color_entry():
    data = ase_bytes([("Base", "#ff8000")])
    block_type = struct.unpack(">H", data[12:14])[0]
    assert block_type == 0x0001  # colour entry
    assert b"RGB " in data
    # 0xff, 0x80, 0x00 -> ~1.0, 0.502, 0.0
    idx = data.index(b"RGB ") + 4
    r, g, b = struct.unpack(">fff", data[idx : idx + 12])
    assert abs(r - 1.0) < 1e-6 and abs(g - 0.502) < 0.01 and b == 0.0
