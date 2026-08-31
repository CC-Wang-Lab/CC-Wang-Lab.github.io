#!/usr/bin/env python3
"""Intrinsic pixel size of a PNG or JPEG, with no third-party dependency.

Pillow would be one import. It is not installed on the CI runner, and the two
gates that need this run there, so the alternative is a `pip install` step on
every push to read eight bytes out of a header.

Only the two formats this site actually ships are supported. Anything else
raises, which is the right answer: a new format is a decision, not an accident.
Checked against Pillow on all 77 figures on 2026-08-31; every size agreed.
"""
from __future__ import annotations

import struct
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Every SOF marker carries the frame size. C4, C8 and CC are not SOF: they are
# the Huffman table, a JPEG extension and the arithmetic-coding table.
SOF_MARKERS = {m for m in range(0xC0, 0xD0)} - {0xC4, 0xC8, 0xCC}


def image_size(path: Path) -> tuple[int, int]:
    """(width, height) in pixels."""
    with open(path, "rb") as fh:
        head = fh.read(8)
        if head == PNG_SIGNATURE:
            # 4-byte length, "IHDR", then width and height as big-endian u32.
            block = fh.read(16)
            if block[4:8] != b"IHDR":
                raise ValueError(f"{path}: PNG with no leading IHDR chunk")
            return struct.unpack(">II", block[8:16])
        if head[:2] != b"\xff\xd8":
            raise ValueError(f"{path}: not a PNG or a JPEG")

        fh.seek(2)
        while True:
            byte = fh.read(1)
            if not byte:
                raise ValueError(f"{path}: JPEG ended before its frame header")
            if byte != b"\xff":
                continue                       # fill byte, or entropy-coded data
            marker = fh.read(1)[0]
            while marker == 0xFF:              # a run of fill bytes is legal
                marker = fh.read(1)[0]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                continue                       # standalone marker, no payload
            length = struct.unpack(">H", fh.read(2))[0]
            if marker in SOF_MARKERS:
                payload = fh.read(5)           # precision, then height, width
                return struct.unpack(">H", payload[3:5])[0], \
                       struct.unpack(">H", payload[1:3])[0]
            fh.seek(length - 2, 1)


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        w, h = image_size(Path(arg))
        print(f"{w} x {h}  {arg}")
