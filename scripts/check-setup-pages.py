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

            # WHICH MECHANISM IS THIS PAGE ON.
            #
            # Both are alive while the 26 records move across. A page that owns
            # its words says so with `\begin{page}`; a page still assembled by
            # utils.jl carries a `blocks` list. The two get different checks,
            # because the parity gate below is TRUE of one and FALSE BY DESIGN
            # of the other.
            owns_words = "\\begin{page}" in en

            # Whitespace-tolerant on purpose. The first version grepped for
            # exactly `lang = "en"`, and a generated page that aligned its
            # front-matter equals signs failed a check that had nothing to do
            # with alignment. A gate should not care how a file is spaced.
            if (not re.search(r'^\s*lang\s*=\s*"en"', en, re.M)
                    or not re.search(r'^\s*lang\s*=\s*"zh"', zh, re.M)):
                failures.append(f"{rid}: each page must declare its own lang")

            # EVERY \begin{X} NEEDS ITS \end{X}, on both mechanisms.
            #
            # An unbalanced file fails in one of two ways and NEITHER is
            # visible. A stray \begin kills the build, which at least says so.
            # A stray \end silently drops the wrapper: the page renders, the
            # words are all there, and they are no longer inside a
            # `.setup-notes` div, so they lose their measure, their
            # justification and every type rule the block carries.
            #
            # Found on chip-package-lid-diamond-copper, 2026-09-01, where the
            # English page had two \end{words} and no \begin{words} while its
            # Chinese twin was correct. check-setup-pages, check-setup-content
            # and check-setup-renderer all passed it. Nothing counted the
            # delimiters, so nothing could.
            for path, text in ((english, en), (chinese, zh)):
                for env in ("page", "words", "split", "level"):
                    opens = len(re.findall(r"\\begin\{" + env + r"\}", text))
                    closes = len(re.findall(r"\\end\{" + env + r"\}", text))
                    if opens != closes:
                        failures.append(
                            f"{rid}: {path.name} has {opens} \\begin{{{env}}} and "
                            f"{closes} \\end{{{env}}}; they must match")

            if owns_words:
                # THE FOUR CHECKS THAT REPLACE THE PARITY GATE.
                #
                # The old gate said the two language files differ by exactly one
                # line. Once the words live in the page that is false on purpose,
                # so it is gone. What replaces it is weaker and everyone should
                # know it: nothing here can tell you the Chinese is WRONG, only
                # that it exists and that it shows the same pictures.
                for path, text, want in ((english, en, "en"), (chinese, zh, "zh")):
                    front = text.split("+++")[1]
                    for key in ("title", "lead"):
                        if not re.search(rf'^\s*{key}\s*=\s*"', front, re.M):
                            failures.append(
                                f"{rid}: {path.name} has no `{key}` in its front "
                                f"matter, and the cards read it")
                    body = text.split("+++", 2)[-1]
                    if not re.sub(r"[\\{}~@\s]|begin|end|page|words|level|split|"
                                  r"figrow|setuphead", "", body):
                        failures.append(
                            f"{rid}: {path.name} has no prose at all; an empty "
                            f"translation is worse than an English one")
                # The pictures must not diverge between the languages. Only the
                # words may.
                en_figs = re.findall(r"\{\{figrow ([^}]*)\}\}|\\begin\{(?:level|split)\}\{([^}]*)\}", en)
                zh_figs = re.findall(r"\{\{figrow ([^}]*)\}\}|\\begin\{(?:level|split)\}\{([^}]*)\}", zh)
                if en_figs != zh_figs:
                    failures.append(
                        f"{rid}: the two languages name different figures, or name "
                        f"them in a different order")
                # FULL PARITY, for as long as no real Chinese exists.
                #
                # This architecture lets the two languages differ, because one
                # day the Chinese pages will carry Chinese. Today not one of
                # them holds a character its English twin does not, so any
                # difference is a file somebody forgot, not a translation.
                # supercritical-co2-chiller drifted exactly that way.
                en_lines = [l for l in en.split(chr(10)) if not l.startswith("lang ")]
                zh_lines = [l for l in zh.split(chr(10)) if not l.startswith("lang ")]
                if en_lines != zh_lines:
                    where = next((i for i, (a, b) in enumerate(zip(en_lines, zh_lines))
                                  if a != b), min(len(en_lines), len(zh_lines)))
                    failures.append(
                        f"{rid}: the English and Chinese pages differ beyond the lang "
                        f"line, first at line {where + 1}. Run "
                        f"scripts/mirror-zh.py, which rewrites every Chinese page "
                        f"from its English twin and refuses if one carries real "
                        f"Chinese")
                named = [i for pair in en_figs for grp in pair for i in grp.split()]
                have = [str(f["id"]) for f in record.get("figure", [])]
                for i in named:
                    if i not in have:
                        failures.append(f"{rid}: names figure '{i}', which the record has not got")
                for i in have:
                    if named.count(i) != 1:
                        failures.append(
                            f"{rid}: figure '{i}' appears {named.count(i)} time(s); "
                            f"it must appear exactly once")
                for name in re.findall(r"\{\{\s*([a-z_0-9]+)", en):
                    if name not in known:
                        failures.append(f"{rid}: calls {{{{{name}}}}}, which utils.jl does not define")
                continue

            # 1. parity, line by line, everything but `lang`. OLD MECHANISM ONLY.
            en_lines = [ln for ln in en.split("\n") if not ln.startswith("lang ")]
            zh_lines = [ln for ln in zh.split("\n") if not ln.startswith("lang ")]
            if en_lines != zh_lines:
                first = next((i for i, (a, b) in enumerate(zip(en_lines, zh_lines)) if a != b),
                             min(len(en_lines), len(zh_lines)))
                failures.append(
                    f"{rid}: the English and Chinese pages differ beyond the lang line, "
                    f"first at line {first + 1}")

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
