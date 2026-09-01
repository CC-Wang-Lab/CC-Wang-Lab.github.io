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
Also measured. Across the whole set, palette PNG is 419 KB against 1,595 KB for
truecolour and 841 KB for WebP. A logo is flat colour, so the palette is usually
exact. It is only used where the error against the truecolour render is below
`PALETTE_RMSE_MAX`; a mark with a gradient keeps its full colour.

HABITS THIS SCRIPT KEEPS, PAID FOR ON 2026-08-31
1. It copies `partners.toml` before touching it.
2. It re-parses the TOML after writing and restores the copy if the parse fails.
3. It resets its per-record state on `[[org]]`, never on a sub-table.
"""

from __future__ import annotations

import argparse
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

DPR = 3                  # the asset is rendered at 3x its display size
PALETTE_RMSE_MAX = 2.0   # 0-255 scale, over the composited-on-white render
PAD = 10                 # every key in _data/*.toml is padded to 10 columns


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
    tmp = Path(tempfile.mkstemp(suffix=".png")[1])
    subprocess.run(["magick", "-background", "none", "-density", "600",
                    str(path), "-resize", f"x{height}", str(tmp)],
                   check=True, capture_output=True)
    return Image.open(tmp).convert("RGBA")


def display_size(aspect: float, ink: float) -> tuple[float, float]:
    h = H0 * (AR_REF / aspect) ** P * (INK_REF / ink) ** Q
    h = min(max(h, H_MIN), H_MAX)
    w = aspect * h
    if w > W_MAX:
        w = W_MAX
        h = w / aspect
    return w, h


def measure(path: Path) -> tuple[Image.Image, float, float]:
    mark = trim(raster(path))
    alpha = np.asarray(mark).astype(float)[..., 3] / 255.0
    return mark, mark.width / mark.height, float(alpha.mean())


# --- writing --------------------------------------------------------------

def on_white(a: np.ndarray) -> np.ndarray:
    al = a[..., 3:4] / 255.0
    return a[..., :3] * al + 255.0 * (1.0 - al)


def write_png(mark: Image.Image, out: Path, w_px: float, h_px: float) -> int:
    """Render at DPR, then keep the smaller of truecolour and palette - but only
    where the palette is visually exact."""
    target = (max(1, round(w_px * DPR)), max(1, round(h_px * DPR)))
    small = mark.resize(target, Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    small.save(out, optimize=True)
    subprocess.run(["magick", str(out), "-strip",
                    "-define", "png:compression-filter=5",
                    "-define", "png:compression-level=9", str(out)], capture_output=True)
    full = out.stat().st_size

    pal = out.with_suffix(".pal.png")
    subprocess.run(["magick", str(out), "-strip", "-colors", "256",
                    "-define", "png:color-type=3", str(pal)], capture_output=True)
    if pal.exists():
        a = np.asarray(Image.open(pal).convert("RGBA"), dtype=float)
        b = np.asarray(small.convert("RGBA"), dtype=float)
        rmse = float(np.sqrt(np.mean((on_white(a) - on_white(b)) ** 2)))
        if rmse <= PALETTE_RMSE_MAX and pal.stat().st_size < full:
            pal.replace(out)
        else:
            pal.unlink()
    return out.stat().st_size


def update_toml(sizes: dict[str, tuple[str, int, int]]) -> None:
    """Set `logo`, `w` and `h` on each row, keyed by name_en.

    A copy is taken first and restored if the result does not parse. State is
    reset on `[[org]]` and on nothing else.
    """
    backup = TOML.with_suffix(".toml.bak")
    shutil.copy2(TOML, backup)

    text = TOML.read_text(encoding="utf-8")
    out: list[str] = []
    current: str | None = None
    pending: tuple[str, int, int] | None = None

    def flush() -> None:
        """Write logo/w/h for the row that just ended."""
        nonlocal pending
        if pending:
            logo, w, h = pending
            out.append(f"{'logo':<{PAD}}= \"{logo}\"")
            out.append(f"{'w':<{PAD}}= {w}")
            out.append(f"{'h':<{PAD}}= {h}")
            pending = None

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[["):
            flush()
            current = None
        if current is not None and (stripped.startswith("logo") or
                                    stripped.startswith("w ") or stripped.startswith("w=") or
                                    stripped.startswith("h ") or stripped.startswith("h=")):
            continue          # dropped; rewritten by flush()
        if stripped.startswith("name_en"):
            current = stripped.split("=", 1)[1].strip().strip('"')
            pending = sizes.get(current)
        if current is not None and pending and stripped.startswith("kind"):
            out.append(line)
            flush()
            continue
        out.append(line)
    flush()

    TOML.write_text("\n".join(out), encoding="utf-8")
    try:
        tomllib.load(TOML.open("rb"))
    except Exception as exc:                       # pragma: no cover - guard path
        shutil.copy2(backup, TOML)
        sys.exit(f"partners.toml did not parse after the rewrite, restored: {exc}")


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

        mark, aspect, ink = measure(path)
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

    if args.mock:
        mock(entries, args.mock)
        print(f"\nmock strip -> {args.mock}")
        return 0
    if args.dry_run:
        return 0

    print(f"\n{len(built)} logos, {total:.0f} KB total, {total/max(len(built),1):.1f} KB mean")
    update_toml(built)
    print(f"wrote logo/w/h into {TOML.relative_to(ROOT)} (copy at partners.toml.bak)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
