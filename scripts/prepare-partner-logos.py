#!/usr/bin/env python3
"""Build the partner-strip logo assets, and write each one's display size.

WHAT THIS SOLVES
A logo strip that sizes every mark by one `max-height` looks broken, because the
marks are not one shape. Across this set the aspect ratio runs from 0.77 to 10.0
and the ink coverage from 17% to 100%. A 10:1 wordmark pinned to the same height
as a square badge is a thin sliver beside a heavy block.

So each logo gets its OWN display size, computed from two measured numbers:

    h = H0 * (AR_REF/aspect)^P * (INK_REF/ink)^Q      clamped to [H_MIN, H_MAX]
    w = aspect * h                                    clamped to  W_MAX

`aspect` is width/height of the TRIMMED mark. `ink` is its mean alpha, which is
how much of that box the mark actually paints. A pale, airy mark is drawn a
little larger; a solid filled block a little smaller. Neither term is allowed to
run away, which is what the clamps are for.

The exponents are not derived from anything. They were tuned by rendering the
whole strip at real size and looking at it. Re-tune the same way:

    python scripts/prepare-partner-logos.py --mock _tmp/strip.png

WHY PNG AND NOT TRACED SVG
Measured on 12 of these files, 2026-09-01. A traced SVG came out **14x heavier**
than the same logo as an optimised PNG (2,440 KB against 179 KB), and it was not
even faithful - one file reached 1.4 MB on its own. A trace of an anti-aliased
raster spends its curves on the anti-aliasing. Where a real vector file exists
it is kept and never re-traced; see `_assets/img/partners/SOURCES.md`.

WHY A 256-COLOUR PALETTE
Also measured, over all 60 raster logos at 3x display size:

    truecolour PNG      1,622 KB
    WebP lossless       1,121 KB
    WebP q=92             901 KB
    256-colour PNG        422 KB      <- 3.8x lighter than truecolour

A logo is flat colour, so a 256-entry palette is usually exact. Usually, not
always: 22 of the 60 came out over 2 RMSE and the worst reached 7.9, which is a
visible band across a gradient. So the palette is taken per FILE, only where the
error against the truecolour render is under `PALETTE_RMSE_MAX`. A mark with a
gradient keeps its full colour.

HABITS THIS SCRIPT KEEPS, PAID FOR ON 2026-08-31
1. It copies `partners.toml` before touching it.
2. It re-parses the TOML after writing and restores the copy if the parse fails.
3. It resets its per-record state on `[[org]]`, never on a sub-table.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "_assets" / "img" / "partners"
TOML = ROOT / "_data" / "partners.toml"
DEFAULT_SOURCE = ROOT.parent / "_internal-docs" / "logo-originals"
DEFAULT_MAP = ROOT.parent / "_internal-docs" / "partner-logo-map.toml"

# --- the sizing law -------------------------------------------------------
# CSS pixels at a 16px root. These are the caps in `.pt-logo`; keep them equal.
H_MAX, W_MAX, H_MIN = 48.0, 192.0, 20.0
AR_REF, INK_REF = 3.8, 0.33
P, Q, H0 = 0.42, 0.22, 34.0

# The asset is rendered at DPR x its display size. 2, not 3.
#
# A logo here is at most 192x48 CSS px, so a 2x asset is 384x96. Rendered side
# by side at 3x device pixels on 2026-09-01, the 2x asset upscaled and the 3x
# asset were separable only in the finest CJK subtitles, and on a real 3x phone
# the mark is 48 px tall and the difference is gone. 3x cost 807 KB across the
# 60 raster logos; 2x costs 360 KB for the same picture.
#
# This is the same call media.md already makes for the slide crops: nothing on
# this site renders wider than 1320 CSS px, so pixels above that are weight
# nobody sees.
DPR = 2
PALETTE_RMSE_MAX = 3.0   # 0-255 scale, over the composited-on-white render
PALETTE_COLOURS  = 256
PAD = 8                  # partners.toml pads every key to 8 columns


# --- measuring ------------------------------------------------------------

def trim(im: Image.Image) -> Image.Image:
    """Crop away fully transparent margin. Without this a logo that occupies 3%
    of its canvas renders as a speck while its neighbour fills the box."""
    a = np.asarray(im.convert("RGBA"))
    mask = a[..., 3] > 8
    if not mask.any():
        return im
    ys, xs = np.where(mask)
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def raster(path: Path, height: int = 600) -> Image.Image:
    """Load a PNG, or render an SVG through ImageMagick's librsvg."""
    if path.suffix.lower() != ".svg":
        return Image.open(path).convert("RGBA")
    fd, name = tempfile.mkstemp(suffix=".png")
    os.close(fd)                      # Windows keeps the handle, and magick cannot write over it
    tmp = Path(name)
    done = subprocess.run(["magick", "-background", "none", "-density", "600",
                           str(path), "-resize", f"x{height}", str(tmp)],
                          capture_output=True, text=True)
    if done.returncode or not tmp.stat().st_size:
        raise RuntimeError(f"could not render {path.name}: {done.stderr.strip()}")
    image = Image.open(tmp).convert("RGBA")
    tmp.unlink(missing_ok=True)
    return image


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def apply_fix(image: Image.Image, entry: dict, source: Path) -> Image.Image:
    """Repair artwork that cannot survive one of the two themes.

    A logo drawn for a dark background is not a bug in the site, it is a bug in
    the FILE, and the honest place to correct it is here, once, on the way in.
    Each fix names the source size it was measured against and refuses to run on
    anything else, so a replaced original fails loudly instead of being silently
    repainted in the wrong place.
    """
    kind = entry.get("fix", "")
    if not kind:
        return image

    want = tuple(entry["fix_src_size"])
    if image.size != want:
        raise SystemExit(
            f"{source.name}: fix '{kind}' was measured on {want[0]}x{want[1]} "
            f"but this file is {image.size[0]}x{image.size[1]}. Re-measure it.")

    a = np.asarray(image).astype(np.int16).copy()

    if kind == "white-ink-to":
        # White lettering meant for a dark page. Repaint just that lettering,
        # inside the box given, and leave the rest of the mark untouched.
        x0, y0, x1, y1 = entry["fix_box"]
        region = a[y0:y1, x0:x1]
        lum = (0.2126 * region[..., 0] + 0.7152 * region[..., 1] + 0.0722 * region[..., 2])
        ink = (region[..., 3] > 8) & (lum > 200)
        region[..., 0][ink], region[..., 1][ink], region[..., 2][ink] = hex_rgb(entry["fix_colour"])
        a[y0:y1, x0:x1] = region

    elif kind == "unmatte-white":
        # The mark carries its own opaque WHITE plate, so it is a pale rectangle
        # on the light page and a dark one in the dark theme. Undo the matte:
        # a pixel is ink laid over white, so recover both the ink and how much
        # of it there is. c = a*F + (1-a)*255, with a = 1 - min(c)/255.
        opaque = a[..., 3] > 200
        c = a[..., :3].astype(float)
        alpha = 1.0 - c.min(axis=2) / 255.0
        safe = np.maximum(alpha, 1e-6)[..., None]
        front = np.clip((c - (1.0 - alpha[..., None]) * 255.0) / safe, 0, 255)
        a[..., :3] = np.where(opaque[..., None], front.astype(np.int16), a[..., :3])
        a[..., 3] = np.where(opaque, np.round(alpha * 255).astype(np.int16), a[..., 3])

    else:
        raise SystemExit(f"{source.name}: unknown fix '{kind}'")

    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def display_size(aspect: float, ink: float) -> tuple[float, float]:
    h = H0 * (AR_REF / aspect) ** P * (INK_REF / ink) ** Q
    h = min(max(h, H_MIN), H_MAX)
    w = aspect * h
    if w > W_MAX:
        w = W_MAX
        h = w / aspect
    return w, h


def measure(path: Path, entry: dict) -> tuple[Image.Image, float, float]:
    mark = trim(apply_fix(raster(path), entry, path))
    alpha = np.asarray(mark).astype(float)[..., 3] / 255.0
    return mark, mark.width / mark.height, float(alpha.mean())


# --- writing --------------------------------------------------------------

def on_white(a: np.ndarray) -> np.ndarray:
    al = a[..., 3:4] / 255.0
    return a[..., :3] * al + 255.0 * (1.0 - al)


def write_png(mark: Image.Image, out: Path, w_px: float, h_px: float) -> int:
    """Render at DPR, then keep a 256-colour copy only where it is faithful.

    Measured across all 60 raster logos on 2026-09-01, at 3x display size:

        truecolour PNG      1,622 KB
        WebP lossless       1,121 KB
        256-colour PNG        422 KB      <- 3.8x lighter
        WebP q=92             901 KB

    So the palette is the win, and a logo is flat colour so it is usually exact.
    It is not always exact: 22 of the 60 came out over 2 RMSE, and the worst
    reached 7.9, which is a visible band across a gradient. Those keep their
    full colour. The gate is per file, not per set.

    DO NOT force `png:color-type=3`. The first version did, and it threw the
    alpha channel away: every logo came back on an opaque black field, at
    RMSE 212. The size looked wonderful and the images were destroyed. Let
    ImageMagick choose the PNG type after `-colors`.
    """
    target = (max(1, round(w_px * DPR)), max(1, round(h_px * DPR)))
    small = mark.resize(target, Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    small.save(out, optimize=True)
    subprocess.run(["magick", str(out), "-strip",
                    "-define", "png:compression-filter=5",
                    "-define", "png:compression-level=9", str(out)], capture_output=True)
    full = out.stat().st_size

    reference = np.asarray(small.convert("RGBA"), dtype=float)
    palette = out.with_suffix(".pal.png")
    subprocess.run(["magick", str(out), "-strip", "-colors", str(PALETTE_COLOURS),
                    "-define", "png:compression-level=9", str(palette)], capture_output=True)
    if palette.exists():
        got = np.asarray(Image.open(palette).convert("RGBA"), dtype=float)
        same_shape = got.shape == reference.shape
        rmse = (float(np.sqrt(np.mean((on_white(got) - on_white(reference)) ** 2)))
                if same_shape else 1e9)
        if rmse <= PALETTE_RMSE_MAX and palette.stat().st_size < full:
            palette.replace(out)
        else:
            palette.unlink()
    return out.stat().st_size


def update_toml(sizes: dict[str, tuple[str, int, int]]) -> None:
    """Set `logo`, `w` and `h` on each row, keyed by name_en.

    A copy is taken first and restored if the result does not parse. State is
    reset on `[[org]]` and on nothing else.

    `replacing` is deliberately separate from `pending`. flush() clears
    `pending` the moment the new keys are written, and that happens at the
    `kind` line, which is BEFORE the old `logo` line is read. Testing the old
    lines against `pending` therefore let the old `logo` through and the key
    landed twice.
    """
    backup = TOML.with_suffix(".toml.bak")
    shutil.copy2(TOML, backup)

    out: list[str] = []
    current: str | None = None
    pending: tuple[str, int, int] | None = None
    replacing = False

    def flush() -> None:
        nonlocal pending
        if pending:
            logo, w, h = pending
            out.append(f"{'logo':<{PAD}}= \"{logo}\"")
            out.append(f"{'w':<{PAD}}= {w}")
            out.append(f"{'h':<{PAD}}= {h}")
            pending = None

    for line in TOML.read_text(encoding="utf-8").split("\n"):
        stripped = line.strip()
        if stripped.startswith("[["):
            flush()
            current, replacing = None, False
        if stripped.startswith("name_en"):
            current = stripped.split("=", 1)[1].strip().strip('"')
            pending = sizes.get(current)
            replacing = pending is not None
        key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
        # A row that is GETTING a logo loses its old logo/w/h. A row with none
        # keeps its `logo = ""` exactly as it was.
        if replacing and key in ("logo", "w", "h"):
            continue
        out.append(line)
        if replacing and key == "kind":
            flush()

    TOML.write_text("\n".join(out), encoding="utf-8")
    try:
        rows = tomllib.load(TOML.open("rb"))["org"]
    except Exception as exc:
        shutil.copy2(backup, TOML)
        sys.exit(f"partners.toml did not parse after the rewrite, restored: {exc}")

    written = {r["name_en"] for r in rows if r.get("logo")}
    missed = set(sizes) - written
    if missed:
        shutil.copy2(backup, TOML)
        sys.exit(f"these logos never reached a row, restored: {sorted(missed)}")
    for r in rows:
        if r.get("logo"):
            assert r.get("w", 0) > 0 and r.get("h", 0) > 0, r["name_en"]
    print(f"{len(written)} rows now carry a logo with a size")


SOURCES_HEAD = """# Partner logos - where each file came from

**This file is generated.** `scripts/prepare-partner-logos.py` writes it from
`_data/partners.toml` and `../_internal-docs/partner-logo-map.toml`, so a logo
cannot arrive without its row. Do not edit it by hand; edit the map and re-run.

## How these were obtained

Two sources, and they are not equal.

**The lab's own set, {lab} files, supplied 2026-09-01.** This is what
`NEEDED.md` had been asking for since 2026-08-19: the collage the lab already
uses to show who it works with. It is both more reliable and more defensible
than hunting each company's website, because somebody at the lab chose it.

**Wikimedia Commons, {wiki} files, downloaded 2026-08-19.** Kept only where the
artwork is the SAME mark as the lab's own file. A real vector beats a raster at
every size, so where the two agree the vector wins. Where they disagree, the
lab's file wins and the reason is written beside the row.

Every file was looked at, one by one, before being accepted. That check is not
optional:

- A search for "ASE Group logo" returned **the European Space Agency banner**.
- A search for "Lite-On logo" returned an unrelated mark reading "TL".
- A search for "Google logo" returned the **Google Play** logo from 2012-2015.

All three were rejected. A logo that is nearly right is worse than a name in
plain text, because a visitor who knows the company sees the mistake at once.

## What was done to each file

Nothing that changes the mark, except where a row says so.

1. **Trimmed.** Several arrived with the mark occupying under 5% of the canvas.
2. **Sized.** Each logo gets its own display size from its aspect ratio and ink
   coverage, so a 10:1 wordmark is not a sliver beside a square badge. The law
   is in `scripts/prepare-partner-logos.py`.
3. **Rendered at 3x** that size and optimised.
4. **Repaired, two of them only.** A mark drawn in white for a dark background
   cannot survive this site's light theme. Those rows carry a `fix` note.

**No logo was traced to SVG.** Measured on 12 of these files: a traced SVG came
out 14x heavier than the same logo as an optimised PNG, 2,440 KB against 179 KB,
and was not faithful either. One file reached 1.4 MB on its own.

## Copyright

The Wikimedia files are **public domain**: simple wordmarks below the threshold
of originality, so no copyright subsists and there is no licence to comply with.

The lab's own files are the marks of the organisations named. **Public domain
for copyright is not permission for trademark**, and that question is handled by
how the logos are used, not by where the files came from:

- The heading reads **"Organizations we have worked with"**, which states a
  fact. It is not "Our clients" and not "Trusted by", either of which would
  imply endorsement.
- A notice under the strip says the marks belong to their owners and that no
  endorsement is implied.
- Logos render greyscale until hover, which uses less of each mark.

**The NDA question is still open and is not a question this file can answer.**
A non-disclosure agreement often forbids revealing that a relationship exists at
all. Prof. Wang's office must mark every organisation whose agreement forbids
disclosure, and those rows must be DELETED from `_data/partners.toml`.

## The files
"""


def write_docs(entries: list[tuple[str, str, str, str]], rows: list[dict]) -> None:
    """Rewrite SOURCES.md and NEEDED.md from what was actually built."""
    wiki = sum(1 for e in entries if e[2].endswith(".svg"))
    lab = len(entries) - wiki
    by_name = {r["name_en"]: r for r in rows}

    out = [SOURCES_HEAD.format(lab=lab, wiki=wiki), ""]
    out.append("| File | Organisation | Source | Note |")
    out.append("|---|---|---|---|")
    for name, sl, source, why in sorted(entries, key=lambda e: e[0].lower()):
        row = by_name[name]
        asset = Path(row["logo"]).name
        origin = ("Wikimedia Commons, 2026-08-19" if source.endswith(".svg")
                  else f"the lab's own set, `{source}`")
        note = why or ("" if source.endswith(".svg") else "")
        if row.get("check"):
            note = (note + " " if note else "") + "**Name not yet confirmed by the lab.**"
        out.append(f"| `{asset}` | {name} | {origin} | {note.strip()} |")
    out.append("")

    (ASSETS / "SOURCES.md").write_text("\n".join(out), encoding="utf-8")

    # --- NEEDED.md ---
    missing = [r for r in rows if not r.get("logo")]
    unchecked = [r for r in rows if r.get("check")]
    n = [
        "# Logo files still needed",
        "",
        "**This file is generated** by `scripts/prepare-partner-logos.py`.",
        "",
    ]
    if missing:
        verb = "does" if len(missing) == 1 else "do"
        n += [f"**{len(rows) - len(missing)} of {len(rows)} organisations have a logo. "
              f"{len(missing)} {verb} not**, and render as their name in text until a",
              "file arrives. The strip works either way, so nothing is blocked.",
              "",
              "| Organisation | 中文 |", "|---|---|"]
        n += [f"| {r['name_en']} | {r['name_zh']} |" for r in missing]
    else:
        n += [f"**Every one of the {len(rows)} organisations has a logo.** Nothing is needed here."]
    n += [
        "",
        "## How to add one",
        "",
        "1. Drop the file in `../_internal-docs/logo-originals/`. A PNG with a",
        "   transparent background is fine; a real SVG is better.",
        "2. Add a `[[logo]]` row to `../_internal-docs/partner-logo-map.toml`",
        "   naming the organisation, its slug and that file.",
        "3. Run `python scripts/prepare-partner-logos.py`. It sizes the logo,",
        "   writes the asset, fills `logo`/`w`/`h` in `_data/partners.toml` and",
        "   rewrites `SOURCES.md`.",
        "4. Run `python scripts/check-partner-logos.py`. It fails a logo that",
        "   disappears in either theme.",
        "",
        "**Look at every file before accepting it.** Searching by name is",
        "unreliable: \"ASE Group logo\" returned the European Space Agency banner,",
        "\"Lite-On logo\" an unrelated mark reading \"TL\", and \"Google logo\" the",
        "2012 Google Play logo. All three would have been visible errors.",
        "",
    ]
    if unchecked:
        n += [
            "## Names still to be confirmed by the lab",
            "",
            f"These {len(unchecked)} rows carry `check = true`. Each name was read off the",
            "logo, or off the file name where the mark carries no words, and could",
            "not be settled against a public record.",
            "",
            "| Organisation | 中文 |", "|---|---|",
        ]
        n += [f"| {r['name_en']} | {r['name_zh']} |" for r in unchecked]
        n += [""]
    (ASSETS / "NEEDED.md").write_text("\n".join(n), encoding="utf-8")
    print(f"rewrote SOURCES.md ({len(entries)} rows) and NEEDED.md "
          f"({len(missing)} missing, {len(unchecked)} unconfirmed)")


# --- mock strip -----------------------------------------------------------

def mock(entries: list[tuple[str, Image.Image, float, float]], out: Path,
         per_row: int = 11, gap: int = 52, row_h: int = 56, scale: int = 2) -> None:
    """Render the strip as the CSS paints it - greyscale at 62% - so the sizing
    law can be judged by eye rather than argued about."""
    rows = [entries[i:i + per_row] for i in range(0, len(entries), per_row)]
    width = max(sum(round(w * scale) + gap * scale for _, _, w, _ in r) for r in rows) + gap * scale
    canvas = Image.new("RGB", (width, int(len(rows) * row_h * scale) + 20), (255, 255, 255))
    for ri, row in enumerate(rows):
        x = gap * scale // 2
        for _, mark, w, h in row:
            tw, th = max(1, round(w * scale)), max(1, round(h * scale))
            a = np.asarray(mark.resize((tw, th), Image.LANCZOS)).astype(float)
            lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
            grey = Image.fromarray(np.dstack([lum, lum, lum, a[..., 3] * 0.62]).astype(np.uint8))
            flat = Image.alpha_composite(Image.new("RGBA", grey.size, (255,) * 4), grey)
            canvas.paste(flat.convert("RGB"), (x, int(ri * row_h * scale + (row_h * scale - th) // 2) + 10))
            x += tw + gap * scale
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


# --- main -----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                    help="folder of original logo files")
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP,
                    help="TOML mapping each organisation to its source file")
    ap.add_argument("--mock", type=Path, default=None,
                    help="also render the whole strip to this path and stop")
    ap.add_argument("--dry-run", action="store_true", help="measure only, write nothing")
    args = ap.parse_args()

    if not args.map.exists():
        return print(f"no map at {args.map}") or 1
    mapping = tomllib.load(args.map.open("rb"))["logo"]

    built: dict[str, tuple[str, int, int]] = {}
    provenance: list[tuple[str, str, str, str]] = []
    entries: list[tuple[str, Image.Image, float, float]] = []
    total = 0

    print(f"{'organisation':<42} {'aspect':>6} {'ink':>5} {'display':>10} {'asset':>11} {'KB':>6}")
    for row in mapping:
        name_en, slug, source = row["name_en"], row["slug"], row["source"]
        vector = source.lower().endswith(".svg")
        path = (ASSETS / source) if vector else (args.source / source)
        if not path.exists():
            print(f"{name_en:<42}  MISSING {path}")
            continue

        mark, aspect, ink = measure(path, row)
        w_d, h_d = display_size(aspect, ink)
        entries.append((name_en, mark, w_d, h_d))

        if args.mock or args.dry_run:
            print(f"{name_en:<42} {aspect:>6.2f} {ink:>5.2f} "
                  f"{round(w_d):>4} x {round(h_d):<3} {'':>11} {'':>6}")
            built[name_en] = (f"/assets/img/partners/{source}", round(w_d), round(h_d))
            continue

        if vector:
            out_rel, kb = source, path.stat().st_size / 1024
        else:
            out = ASSETS / f"{slug}.png"
            kb = write_png(mark, out, w_d, h_d) / 1024
            out_rel = out.name
        total += kb
        print(f"{name_en:<42} {aspect:>6.2f} {ink:>5.2f} "
              f"{round(w_d):>4} x {round(h_d):<3} {out_rel:>11} {kb:>6.1f}")
        built[name_en] = (f"/assets/img/partners/{out_rel}", round(w_d), round(h_d))
        provenance.append((name_en, slug, source, row.get("why", "")))

    if args.mock:
        mock(entries, args.mock)
        print(f"\nmock strip -> {args.mock}")
        return 0
    if args.dry_run:
        return 0

    print(f"\n{len(built)} logos, {total:.0f} KB total, {total/max(len(built),1):.1f} KB mean")
    update_toml(built)
    print(f"wrote logo/w/h into {TOML.relative_to(ROOT)} (copy at partners.toml.bak)")
    write_docs(provenance, tomllib.load(TOML.open("rb"))["org"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
