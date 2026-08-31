#!/usr/bin/env python3
"""Write each figure's intrinsic pixel size into the TOML row, beside its image.

The aspect ratio is what sizes a justified row, and w/h on the <img> is what
stops the page reflowing as pictures arrive. Both need the number at BUILD
time, and Franklin cannot open a file mid-template without a new dependency.

The value is a copy of what is on disk, so it can go stale. That is what the
check in check-test-setup-import.py is for.
"""
import re
import sys
import tomllib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from imagesize import image_size

ROOT = Path(__file__).resolve().parent.parent
PAD = 10          # every key in these files is padded to 10 columns


def asset(image: str) -> Path:
    assert image.startswith("/assets/"), image
    return ROOT / "_assets" / image[len("/assets/"):]


for name, key in (("facilities.toml", "item"), ("projects.toml", "project")):
    path = ROOT / "_data" / name
    text = path.read_text(encoding="utf-8")
    table = f"[[{key}.figure]]"

    out, n, changed = [], 0, 0
    in_figure = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[["):
            in_figure = stripped == table
        # a w/h already written by an earlier run of this script
        if in_figure and re.match(r"^[wh]\s+= ", line):
            continue
        out.append(line)
        m = re.match(r'^image\s+= "(/assets/[^"]+)"$', line)
        if in_figure and m:
            w, h = image_size(asset(m.group(1)))
            out.append(f"{'w'.ljust(PAD)} = {w}")
            out.append(f"{'h'.ljust(PAD)} = {h}")
            n += 1
            changed += 1

    new = "\n".join(out)
    path.write_text(new, encoding="utf-8")

    rows = tomllib.loads(new)[key]
    figs = [f for r in rows for f in r.get("figure", [])]
    missing = [f["id"] for f in figs if "w" not in f or "h" not in f]
    assert not missing, f"{name}: no size on {missing}"
    for f in figs:
        on_disk = image_size(asset(f["image"]))
        assert on_disk == (f["w"], f["h"]), f"{f['id']}: {on_disk} != {(f['w'], f['h'])}"
    print(f"{name}: {n} figure rows sized, all {len(figs)} verified against disk")
