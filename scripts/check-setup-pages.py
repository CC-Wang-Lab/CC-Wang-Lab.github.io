#!/usr/bin/env python3
"""
Static gate over the COMPOSITION of every facility and project detail page.

Each of these pages lays itself out, in its own front matter:

    blocks = [
      "notes",
      "row:sintered additively-manufactured",
      "row:test-schematic",
    ]

The build already refuses a composition that drops a figure, names one twice,
names one the record has not got, or leaves a section unplaced. What the build
cannot see is the two things below.

    1. The English page and the Chinese page must differ by exactly one line,
       the `lang` line. A composition that is only applied to one language is
       the failure this whole architecture exists to prevent: the site would
       be built from one data file and still show two different pages.

    2. Every record must be composed. A record with no `blocks` would fall
       through to nothing, and "nothing" is the silent no-op that put 25 of 26
       records into the wrong grid the last time.

Run:
    python scripts/check-setup-pages.py
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = (("facilities.toml", "item", "facilities", "facility_page"),
           ("projects.toml", "project", "projects", "project_setup_page"))
# `split` takes several figure ids now, and may name which text goes beside
# them: `split(lead sec:1):a b`. The bare `split:a b` form still means the whole
# of the record's words. Eight records open on a lead plus one section and keep
# later sections further down the page, and for those `notes` would wrongly
# drag every later section into the top block.
BLOCK = re.compile(
    r'^\s*"(notes'
    r'|lead'
    r'|sec:\d+'
    r'|split(?:\((?:notes|lead|sec:\d+)(?: (?:notes|lead|sec:\d+))*\))?:[a-z0-9 -]+'
    r'|row:[a-z0-9 -]+)",?\s*$')


def hfun_names() -> set[str]:
    """Every hfun utils.jl actually defines."""
    source = (ROOT / "utils.jl").read_text(encoding="utf-8")
    return set(re.findall(r"^function hfun_([a-z_0-9]+)", source, re.M))


def page_blocks(text: str) -> list[str] | None:
    """The `blocks` list out of a page's front matter, or None if it has none."""
    front = text.split("+++")[1]
    if "blocks" not in front:
        return None
    body = front.split("blocks", 1)[1].split("[", 1)[1].split("]", 1)[0]
    return [line.strip().strip(",").strip('"') for line in body.strip().split("\n")]


def main() -> int:
    failures: list[str] = []
    known = hfun_names()
    checked = 0

    for src, key, folder, hfun in SOURCES:
        with open(ROOT / "_data" / src, "rb") as fh:
            rows = tomllib.load(fh)[key]
        for record in rows:
            if record.get("placeholder", False) or not record.get("figure"):
                continue
            rid = record["id"]
            english = ROOT / folder / f"{rid}.md"
            chinese = ROOT / "zh" / folder / f"{rid}.md"
            for path in (english, chinese):
                if not path.is_file():
                    failures.append(f"{src}: '{rid}' has no page at {path.relative_to(ROOT)}")
            if not (english.is_file() and chinese.is_file()):
                continue
            checked += 1

            en = english.read_text(encoding="utf-8").replace("\r\n", "\n")
            zh = chinese.read_text(encoding="utf-8").replace("\r\n", "\n")

            # 1. parity, line by line, everything but `lang`
            en_lines = [ln for ln in en.split("\n") if not ln.startswith("lang ")]
            zh_lines = [ln for ln in zh.split("\n") if not ln.startswith("lang ")]
            if en_lines != zh_lines:
                first = next((i for i, (a, b) in enumerate(zip(en_lines, zh_lines)) if a != b),
                             min(len(en_lines), len(zh_lines)))
                failures.append(
                    f"{rid}: the English and Chinese pages differ beyond the lang line, "
                    f"first at line {first + 1}")
            if 'lang = "en"' not in en or 'lang = "zh"' not in zh:
                failures.append(f"{rid}: each page must declare its own lang")

            # 2. every record is composed, and every block is a shape the
            #    renderer knows. An unrecognised one stops the build, but a
            #    typo caught here names the page instead of the record.
            blocks = page_blocks(en)
            if blocks is None:
                failures.append(f"{rid}: no `blocks` in the front matter; every detail "
                                f"page composes itself")
                continue
            for entry in blocks:
                if not BLOCK.match(f'"{entry}"'):
                    failures.append(f"{rid}: block {entry!r} is not one the renderer knows")
            # `split(` as well as `split:`: the parenthesised form names
            # which text goes beside the pictures, and it carries figure
            # ids exactly the same way. Matching only "split:" reported
            # a page with pictures as having none.
            if not any(b.startswith(("row:", "split:", "split(")) for b in blocks):
                failures.append(f"{rid}: `blocks` places no pictures")

            # 2b. every `sec:N` the page names must exist in the record.
            #
            # The build already refuses this, but only when it reaches that
            # page, and the message names the record rather than the file. It
            # is here because deleting a section from _data/ is a normal edit
            # that leaves the page behind, and the two files are far apart.
            # Caught on immersion-cooling-microchannel-lid, 2026-08-31, after
            # its two sections were merged into the lead: the page still asked
            # for sec:1 and sec:2 and the whole build stopped.
            have = len(record.get("section", []))
            for entry in blocks:
                for n in re.findall(r"sec:(\d+)", entry):
                    if not 1 <= int(n) <= have:
                        failures.append(
                            f"{rid}: blocks name sec:{n}, but the record has "
                            f"{have} section(s)")
            # ...and a record whose words were deleted must not still say
            # "notes", which renders an empty block that still costs its gap.
            if not str(record.get("body_en", "")).strip() and have == 0:
                if any(b == "notes" for b in blocks):
                    failures.append(
                        f"{rid}: blocks name \"notes\", but the record has no "
                        f"lead and no sections; drop it from the page")

            # 3. the one hfun the page calls has to exist. Franklin substitutes
            #    an empty string for an unknown name and only logs a warning, so
            #    a misspelling here would build green and render nothing at all.
            for name in re.findall(r"\{\{\s*([a-z_0-9]+)", en):
                if name not in known:
                    failures.append(f"{rid}: calls {{{{{name}}}}}, which utils.jl does not define")
            if f"{{{{{hfun}}}}}" not in en:
                failures.append(f"{rid}: expected the page to call {{{{{hfun}}}}}")

    print(f"checked {checked} composed detail records")
    if failures:
        print(f"\n{len(failures)} composition problem(s):\n")
        for line in failures:
            print("  " + line)
        return 1
    print("composition clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
