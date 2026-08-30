#!/usr/bin/env python3
"""Audit literal test-setup imports in data and the built Franklin site."""

from __future__ import annotations

import re
import sys
import tomllib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
SITEMAP = SITE / "sitemap.xml"

EXPECTED = {
    "facility": {
        "falling-film-cooling-system": ([2], "c", "two-phase", 4),
        "thermal-fin-natural-convection-chamber": ([7], "a", "heat-exchangers", 1),
        "air-cooler-wind-tunnel": ([8], "b", "electronics-cooling", 1),
        "data-center-air-cooling-facility": ([9, 10], "c", "data-center", 7),
        "two-phase-cold-plate-test-platform": ([11], "a", "two-phase", 1),
        "flooded-evaporator-test-rig": ([12], "b", "two-phase", 2),
        "boiler-surface-test-rig": ([13], "c", "two-phase", 6),
        "three-kilowatt-cold-plate-test-facility": ([15], "a", "two-phase", 2),
        "vapor-compression-cooling-system": ([16], "b", "hvacr", 2),
        "refrigerant-lubricant-boiling-system": ([17], "c", "two-phase", 3),
        "liquid-desiccant-air-conditioning-system": ([18], "a", "hvacr", 3),
        "carvera-desktop-cnc": ([28], "b", "electronics-cooling", 1),
        "fabrication-and-microscopy-equipment": ([29], "c", "electronics-cooling", 3),
        "amca-wind-tunnel": ([30], "a", "heat-exchangers", 1),
    },
    "project": {
        "gaming-laptop-hybrid-vapor-chamber": ([3], "a", "electronics-cooling", 2),
        "two-phase-closed-loop-thermosyphon": ([4], "b", "two-phase", 3),
        "chip-package-lid-thermal-spreading": ([5, 6], "c", "electronics-cooling", 7),
        "heat-pipes-freezing-conditions": ([14], "a", "two-phase", 2),
    },
}

PLURAL = {"facility": "facilities", "project": "projects"}
EXPECTED_COUNTS = {"facility": 14, "project": 4}
EXPECTED_LAYOUTS = {
    "facility": {"a": 5, "b": 4, "c": 5},
    "project": {"a": 2, "b": 1, "c": 1},
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.classes: list[set[str]] = []

    def handle_starttag(self, _tag: str, attrs) -> None:
        values = dict(attrs)
        self.classes.append(set((values.get("class") or "").split()))

    def has_class(self, class_name: str) -> bool:
        return any(class_name in classes for classes in self.classes)


def load_records(kind: str) -> dict[str, dict]:
    path = ROOT / "_data" / f"{PLURAL[kind]}.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return {
        record.get("id", ""): record
        for record in data.get("item" if kind == "facility" else "project", [])
        if not record.get("placeholder")
    }


def source_asset(image: object) -> Path | None:
    if not isinstance(image, str) or not image.startswith("/assets/"):
        return None
    return ROOT / "_assets" / image.removeprefix("/assets/")


def main() -> int:
    failures: list[str] = []
    sitemap = SITEMAP.read_text(encoding="utf-8") if SITEMAP.is_file() else ""

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(SITEMAP.is_file(), "missing built sitemap: __site/sitemap.xml")

    for kind, expected_records in EXPECTED.items():
        records = load_records(kind)
        imported_records = {
            record_id: record
            for record_id, record in records.items()
            if isinstance(record.get("source_slides"), list)
        }
        require(len(imported_records) == EXPECTED_COUNTS[kind],
                f"expected {EXPECTED_COUNTS[kind]} imported {PLURAL[kind]}, "
                f"found {len(imported_records)}")
        require(set(imported_records) == set(expected_records),
                f"{kind} imported record IDs do not match the literal manifest")
        layouts = Counter(record.get("layout") for record in imported_records.values())
        require(dict(sorted(layouts.items())) == EXPECTED_LAYOUTS[kind],
                f"{kind} layout counts: expected {EXPECTED_LAYOUTS[kind]!r}, "
                f"found {dict(sorted(layouts.items()))!r}")
        for record_id, (slides, layout, area, figure_count) in expected_records.items():
            record = records.get(record_id)
            if record is None:
                failures.append(f"missing {kind} record: {record_id}")
                continue

            require(record.get("source_slides") == slides,
                    f"{kind} {record_id}: expected source_slides {slides!r}")
            require(record.get("layout") == layout,
                    f"{kind} {record_id}: expected layout {layout!r}")
            require(record.get("area") == area,
                    f"{kind} {record_id}: expected area {area!r}")
            figures = record.get("figure", [])
            require(isinstance(figures, list) and len(figures) == figure_count,
                    f"{kind} {record_id}: expected {figure_count} figures")
            for field in ("title", "lead", "body"):
                require(record.get(f"{field}_en") == record.get(f"{field}_zh"),
                        f"{kind} {record_id}: {field}_en and {field}_zh must match")
            for section in record.get("section", []):
                for field in ("heading", "body", "items"):
                    require(section.get(f"{field}_en") == section.get(f"{field}_zh"),
                            f"{kind} {record_id}: section {field}_en and {field}_zh must match")
            if isinstance(figures, list):
                for figure in figures:
                    require(figure.get("caption_en") == figure.get("caption_zh"),
                            f"{kind} {record_id}: figure captions must match")

            images = [record.get("image")]
            if isinstance(figures, list):
                images.extend(figure.get("image") for figure in figures
                              if isinstance(figure, dict))
            for image in images:
                asset = source_asset(image)
                require(asset is not None,
                        f"{kind} {record_id}: invalid source asset path: {image!r}")
                if asset is not None:
                    require(asset.is_file(),
                            f"{kind} {record_id}: missing source asset: {image}")

            plural = PLURAL[kind]
            for lang_prefix in ("", "zh/"):
                relative = f"{lang_prefix}{plural}/{record_id}/index.html"
                path = SITE / relative
                route = "/" + relative.removesuffix("index.html")
                require(path.is_file(), f"missing built route: {relative}")
                require(relative.replace("/", "\\") in sitemap,
                        f"{route}: missing from sitemap.xml")
                if not path.is_file():
                    continue
                html = path.read_text(encoding="utf-8")
                page = Page()
                page.feed(html)
                require(page.has_class(f"setup-study--{layout}"),
                        f"{route}: expected setup-study--{layout}")
                require(re.search(r"Slide[^/\\\"']*\.jpg", html, re.IGNORECASE) is None,
                        f"{route}: generated HTML references a source Slide*.jpg")

    if failures:
        print("TEST SETUP IMPORT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("TEST SETUP IMPORT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
