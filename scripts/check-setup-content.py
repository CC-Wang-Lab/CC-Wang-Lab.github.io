#!/usr/bin/env python3
"""
Static gate over the CONTENT of every facility and project record in _data/.

These pages were imported from a slide deck, and a slide carries marks that mean
nothing on a web page: a bullet arrow drawn as a character, a hand-typed "1."
in front of a list item that is already inside a <ul>, a heading with nothing
under it because its content was a picture. None of that is visible to a
stylesheet, none of it fails a build, and all of it reaches the reader.

Run:
    python scripts/check-setup-content.py

Every check below fired on real data on 2026-08-31. None of them is theoretical.
"""
from __future__ import annotations

import re
import sys
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = (("facilities.toml", "item"), ("projects.toml", "project"))

# Characters a slide uses as a bullet or an arrow and a web page must not.
# Listed by code point, because several of them are indistinguishable on screen
# from one another and from a hyphen at small sizes.
SLIDE_MARKS = {
    "▲": "BLACK UP-POINTING TRIANGLE",
    "▶": "BLACK RIGHT-POINTING TRIANGLE",
    "➢": "THREE-D TOP-LIGHTED RIGHTWARDS ARROWHEAD",
    "➤": "BLACK RIGHTWARDS ARROWHEAD",
    "✓": "CHECK MARK",
    "✔": "HEAVY CHECK MARK",
    "•": "BULLET",
    "▪": "BLACK SMALL SQUARE",
    "●": "BLACK CIRCLE",
    "❖": "BLACK DIAMOND MINUS WHITE X",
    "§": "SECTION SIGN",
}
# A list item that numbers itself, inside a <ul> that already numbers it.
SELF_NUMBERED = re.compile(r"^\s*\(?\d+\s*[.)]\s+")
LANGS = ("en", "zh")


def visible_strings(record: dict):
    """Every string this record puts in front of a reader, with its TOML key."""
    for lang in LANGS:
        for key in ("title", "lead", "body"):
            value = record.get(f"{key}_{lang}")
            if isinstance(value, str) and value.strip():
                yield f"{key}_{lang}", value
        for i, fig in enumerate(record.get("figure", [])):
            value = fig.get(f"caption_{lang}")
            if isinstance(value, str) and value.strip():
                yield f"figure[{i}={fig.get('id')}].caption_{lang}", value
        for i, sec in enumerate(record.get("section", [])):
            for key in ("heading", "body"):
                value = sec.get(f"{key}_{lang}")
                if isinstance(value, str) and value.strip():
                    yield f"section[{i}].{key}_{lang}", value
            for j, item in enumerate(sec.get(f"items_{lang}", []) or []):
                if isinstance(item, str) and item.strip():
                    yield f"section[{i}].items_{lang}[{j}]", item


def check(record: dict, src: str, fail):
    rid = record.get("id", "?")
    where = f"{src}: {rid}"

    # 1. A slide mark anywhere in a visible string.
    for key, value in visible_strings(record):
        for ch in value:
            if ch in SLIDE_MARKS:
                fail(f"{where}: {key} contains {SLIDE_MARKS[ch]} "
                     f"(U+{ord(ch):04X}) -- {value[:60]!r}")
                break

    # 2. A list item that numbers itself inside a generated <ul>.
    for i, sec in enumerate(record.get("section", [])):
        for lang in LANGS:
            for j, item in enumerate(sec.get(f"items_{lang}", []) or []):
                if isinstance(item, str) and SELF_NUMBERED.match(item):
                    fail(f"{where}: section[{i}].items_{lang}[{j}] starts with its "
                         f"own number inside a <ul> -- {item[:50]!r}")

    # 3. A heading with nothing under it is ALLOWED, and this check is gone.
    #
    # It fired on four headings and they were deleted. That was wrong twice
    # over. The site owner has since said the wording must match the slide deck
    # exactly, and these are slide labels: "Test Samples" and "Photograph of
    # the setup" name the pictures that follow them. In the row layout a
    # heading labels the row beneath it, which is what they were always for.
    #
    # What the old check was really seeing is a heading rendered in a column
    # far away from the figures it names. That is a layout fault, and deleting
    # the words was the wrong place to fix it.

    # 4. A heading that restates the page title is ALLOWED, and this check is
    # gone as well.
    #
    # chip-package-lid-thermal-spreading has a section headed "Experimental
    # Investigation on Thermal Spreading of Chip Package Lids On Diamond-copper
    # composite Lid", which repeats the first eight words of its own title. It
    # reads oddly, and it is what the slide says. Wording fidelity to the deck
    # wins; a heading that is too long for its column is a layout problem.

    # 5. Two figures sharing one caption, when they are NOT next to each other.
    #
    # Adjacency is the whole test, and it was added after checking the source.
    # Slide 10 of the deck labels two views of the rack "Simulated rack", once
    # each, and slide 29 labels two instruments "Microscope". The repetition is
    # in the source and it is deliberate: a pair of panels sharing one label.
    # Rejecting that would force a caption nobody wrote.
    #
    # Two figures with the same caption and something else in between is a
    # different thing. Nothing ties them together, so the reader sees the same
    # words on unrelated pictures, and that is a mistake worth failing on.
    for lang in LANGS:
        figures = record.get("figure", [])
        seen: dict[str, int] = {}
        for i, fig in enumerate(figures):
            cap = (fig.get(f"caption_{lang}") or "").strip()
            if not cap:
                continue
            if cap in seen and i - seen[cap] > 1:
                fail(f"{where}: figures {figures[seen[cap]].get('id')!r} and "
                     f"{fig.get('id')!r} share caption_{lang} {cap[:40]!r} but are "
                     f"not adjacent")
            seen[cap] = i

    # 6. lead == body is ALLOWED, and this check is gone too.
    #
    # It fired on four records and each lead was shortened to the body's first
    # sentence. Same reasoning as above: the words are the slide's, and the
    # real fault is that the index card prints all 736 of them. A card clamps
    # its own text; it does not get to edit the source.


def main() -> int:
    failures: list[str] = []
    fail = failures.append
    total = 0
    for src, key in SOURCES:
        with open(ROOT / "_data" / src, "rb") as fh:
            rows = tomllib.load(fh)[key]
        for row in rows:
            if row.get("placeholder", False):
                continue
            if not row.get("figure"):
                continue          # a hand-written prose page, not an import
            total += 1
            check(row, src, fail)

    print(f"checked {total} imported detail records")
    if failures:
        print(f"\n{len(failures)} content defect(s):\n")
        for line in failures:
            print("  " + line)
        return 1
    print("content clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
