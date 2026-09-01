#!/usr/bin/env python3
"""Does every partner logo survive BOTH themes?

The strip paints a logo through a filter, and the filter is not the same in the
two themes:

    light   grayscale(1)                        at 62% opacity on #fdfcfa
    dark    grayscale(1) invert(1) brightness(1.6)  at 62% opacity on #14141e

A mark drawn in white ink for a dark background disappears completely in the
light theme, and nothing in the build says so. It happened on 2026-09-01 with
國家中山科學研究院, whose lockup is a dark seal beside WHITE text: the seal showed,
the seven characters beside it did not, and the strip looked like it had a hole
in it.

So this measures what a visitor actually sees. For each logo it computes the
contrast of the mark's own ink against the page it sits on, in each theme, and
fails a logo that is invisible in either.

WHY THIS IS NOT A WCAG GATE
WCAG 1.4.11 exempts logotypes from the contrast minimum, so nothing here is a
conformance failure. The threshold is a legibility floor picked by looking at
the strip, not a standard. `scripts/check-contrast.py` is the WCAG gate and this
is not part of it.

    python scripts/check-partner-logos.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOML = ROOT / "_data" / "partners.toml"

LIGHT_BG = (0xFD, 0xFC, 0xFA)
DARK_BG = (0x14, 0x14, 0x1E)
OPACITY = 0.62
DARK_BRIGHTNESS = 1.6

# A logo below this against its own page reads as a hole in the row. Chosen by
# looking at the rendered strip, not taken from a standard.
FLOOR = 1.30
# Share of the mark's ink allowed to sit under the floor before it is a failure.
# A logo legitimately carries a pale highlight or a soft shadow; a logo whose
# WORDS are pale is the fault this catches.
MAX_FAINT = 0.35

# The measure cannot tell a pale BACKGROUND from pale LETTERING, and both push
# the same number up. These two were rendered at strip size and looked at, in
# both themes, on 2026-09-01. Each one's pale half is decoration and every
# informative part of the mark reads. A named exception with its reason is more
# honest than a threshold tuned until the list came out empty.
#
# Delete an entry rather than edit it if its artwork is ever replaced.
ALLOWED_FAINT = {
    "TSMC": "the pale pixels are the WHITE squares of the wafer chequerboard. "
            "The red 'tsmc' wordmark and the dark squares carry the mark.",
    "Patech Fine Chemicals": "the pale pixels are the mint-green oval the name "
            "sits on. The word 'Patech' itself is near-black and reads.",
}


def raster(path: Path) -> Image.Image:
    if path.suffix.lower() != ".svg":
        return Image.open(path).convert("RGBA")
    fd, name = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    subprocess.run(["magick", "-background", "none", "-density", "600",
                    str(path), "-resize", "x400", name], capture_output=True)
    image = Image.open(name).convert("RGBA")
    Path(name).unlink(missing_ok=True)
    return image


def relative_luminance(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    lin = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def faint_fraction(image: Image.Image, theme: str) -> tuple[float, float]:
    """Share of ink pixels under the floor, and the median contrast."""
    a = np.asarray(image).astype(float)
    grey = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    if theme == "dark":
        value = np.clip((255.0 - grey) * DARK_BRIGHTNESS, 0, 255)
        bg = np.array(DARK_BG, dtype=float)
    else:
        value = grey
        bg = np.array(LIGHT_BG, dtype=float)

    alpha = (a[..., 3] / 255.0) * OPACITY
    painted = np.dstack([value] * 3) * alpha[..., None] + bg * (1 - alpha[..., None])

    lum_mark = relative_luminance(painted)
    lum_bg = float(relative_luminance(bg))
    ratio = (np.maximum(lum_mark, lum_bg) + 0.05) / (np.minimum(lum_mark, lum_bg) + 0.05)

    ink = a[..., 3] > 128
    if not ink.any():
        return 1.0, 1.0
    values = ratio[ink]
    return float((values < FLOOR).mean()), float(np.median(values))


def main() -> int:
    rows = tomllib.load(TOML.open("rb"))["org"]
    failures: list[str] = []
    allowed: list[str] = []
    print(f"{'organisation':<46} {'light faint':>11} {'lt med':>7} "
          f"{'dark faint':>11} {'dk med':>7}")
    for row in rows:
        logo = row.get("logo", "")
        if not logo:
            continue
        path = ROOT / "_assets" / logo[len("/assets/"):]
        if not path.exists():
            failures.append(f"{row['name_en']}: {logo} is not on disk")
            continue
        image = raster(path)
        lf, lm = faint_fraction(image, "light")
        df, dm = faint_fraction(image, "dark")
        flag = ""
        if lf > MAX_FAINT or df > MAX_FAINT:
            worst = "light" if lf > df else "dark"
            if row["name_en"] in ALLOWED_FAINT:
                flag = "  (allowed)"
                allowed.append(f"{row['name_en']}: {ALLOWED_FAINT[row['name_en']]}")
            else:
                flag = "  <-- FAILS"
                failures.append(
                    f"{row['name_en']}: {max(lf, df) * 100:.0f}% of its ink is under "
                    f"{FLOOR}:1 in the {worst} theme")
        print(f"{row['name_en']:<46} {lf * 100:>10.0f}% {lm:>7.2f} "
              f"{df * 100:>10.0f}% {dm:>7.2f}{flag}")

    print()
    for a in allowed:
        print(f"allowed: {a}")
    if allowed:
        print()
    if failures:
        print(f"{len(failures)} logo(s) do not survive a theme:")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"all {sum(1 for r in rows if r.get('logo'))} logos are legible in both themes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
