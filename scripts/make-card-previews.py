#!/usr/bin/env python3
"""Cut the card preview for any record that carries a `card_crop`.

A card box is 16/9. Most records need nothing: the picture fills it, and where
centre is the wrong part `card_focus` says which band to keep. That is one word,
it needs no file, and it survives the source picture being swapped.

`card_crop` is for the case `card_focus` cannot reach: a window that is NARROWER
than the source. Measured on supercritical-co2-chiller, whose photograph is a
chiller standing in a room, with a metre of blank wall on one side and shelving
on the other. No horizontal band of the full width avoids the clutter, because
the clutter is beside the subject, not above it.

    card_crop = [x, y, w, h]      a rectangle in the SOURCE picture's pixels

This writes `<stem>.card.jpg` beside the source. The rectangle is the data and
the file is a build artefact: re-runnable, reviewable in a diff, and
`check-setup-pages.py` fails if the rectangle stops fitting the source.

Run:
    python scripts/make-card-previews.py
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imagesize import image_size  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCES = (("facilities.toml", "item"), ("projects.toml", "project"))
# The card box. A crop that is not this shape is a mistake, not a preference:
# the box will crop it again and undo the framing the rectangle was chosen for.
BOX = 16 / 9
TOLERANCE = 0.02


def card_path(image: str) -> Path:
    rel = image.lstrip("/").replace("assets/", "_assets/", 1)
    p = ROOT / rel
    return p.with_suffix("").with_suffix(".card.jpg") if p.suffix else p


def main() -> int:
    problems: list[str] = []
    made = 0
    seen = 0

    for src, key in SOURCES:
        with open(ROOT / "_data" / src, "rb") as fh:
            rows = tomllib.load(fh)[key]
        for r in rows:
            crop = r.get("card_crop")
            if crop is None:
                continue
            seen += 1
            rid = r["id"]
            if not (isinstance(crop, list) and len(crop) == 4
                    and all(isinstance(v, int) for v in crop)):
                problems.append(f"{rid}: card_crop must be four whole numbers, "
                                f"[x, y, w, h]; got {crop!r}")
                continue
            x, y, w, h = crop
            source = ROOT / r["image"].lstrip("/").replace("assets/", "_assets/", 1)
            if not source.is_file():
                problems.append(f"{rid}: {r['image']} is not on disk")
                continue
            sw, sh = image_size(source)
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > sw or y + h > sh:
                problems.append(f"{rid}: card_crop {crop} does not fit inside "
                                f"the {sw}x{sh} source")
                continue
            shape = w / h
            if abs(shape - BOX) / BOX > TOLERANCE:
                problems.append(f"{rid}: card_crop is {shape:.2f}, not 16/9. The card "
                                f"box will crop it again and lose your framing")
                continue

            out = source.with_name(source.stem + ".card.jpg")
            subprocess.run(["magick", str(source), "-crop", f"{w}x{h}+{x}+{y}",
                            "+repage", "-quality", "88", "-strip", str(out)],
                           check=True)
            made += 1
            print(f"  {rid:44} {w}x{h}+{x}+{y}  ->  {out.name}")

    print(f"\n{seen} record(s) carry a card_crop, {made} preview(s) written")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print("  " + p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
