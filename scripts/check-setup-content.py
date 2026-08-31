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

    # 3. A heading with nothing under it.
    for i, sec in enumerate(record.get("section", [])):
        for lang in LANGS:
            heading = (sec.get(f"heading_{lang}") or "").strip()
            body = (sec.get(f"body_{lang}") or "").strip()
            items = sec.get(f"items_{lang}") or []
            if heading and not body and not items:
                fail(f"{where}: section[{i}] heading_{lang} has no body and no "
                     f"items -- {heading[:50]!r}")

    # 4. A section heading that restates the page title.
    for lang in LANGS:
        title = (record.get(f"title_{lang}") or "").strip().lower()
        if len(title) < 20:
            continue
        for i, sec in enumerate(record.get("section", [])):
            heading = (sec.get(f"heading_{lang}") or "").strip().lower()
            if not heading or len(heading) < 20:
                continue
            head_words = heading.split()
            title_words = title.split()
            n = min(len(head_words), len(title_words), 8)
            if n >= 5 and head_words[:n] == title_words[:n]:
                fail(f"{where}: section[{i}].heading_{lang} repeats the first "
                     f"{n} words of the title -- {heading[:50]!r}")

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

    # 6. The lead is the whole body, so the index card carries the whole page.
    for lang in LANGS:
        lead = (record.get(f"lead_{lang}") or "").strip()
        body = (record.get(f"body_{lang}") or "").strip()
        if lead and lead == body and len(lead) > 300:
            fail(f"{where}: lead_{lang} is identical to body_{lang} and is "
                 f"{len(lead)} characters, so the index card shows the whole page")


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
