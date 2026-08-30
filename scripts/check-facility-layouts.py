#!/usr/bin/env python3
"""Audit the retained falling-film layout-pilot routes."""

from __future__ import annotations

import html
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
FACILITY_ID = "falling-film-cooling-system"
LEGACY_SLIDE = "/assets/img/facilities/falling-film-cooling-system.jpg"
FIGURES = (
    (
        "/assets/img/facilities/falling-film-cooling-100w.jpg",
        "Fig. Falling film (100 W)",
    ),
    (
        "/assets/img/facilities/falling-film-cooling-500w.jpg",
        "Fig. Falling film (500 W)",
    ),
    (
        "/assets/img/facilities/falling-film-cooling-cabinet.png",
        "Fig. Perspective view of the experimental cabinet",
    ),
    (
        "/assets/img/facilities/falling-film-cooling-dimensions.png",
        "Fig. Experimental cabinet interior dimensions",
    ),
)
INDEX_IMAGE = FIGURES[2][0]
TITLE = "Two-phase falling-film cooling system"
DESCRIPTION = (
    "This two-phase falling-film cooling system uses 3M™ Electronic "
    "Fluorinated Fluid HFE-7100 as the working fluid and operates as an "
    "atmospheric-pressure closed loop. Experiments were conducted using a "
    "simulated heat source measuring 44 mm × 34 mm × 1 mm. The degree of "
    "subcooling was maintained at 10°C, while flow rates of 500, 700, and 900 "
    "g/min were tested to investigate the effects of flow rate and heat-sink "
    "design on the heat transfer coefficient and temperature distribution. At "
    "the same flow rate, increasing the power input expanded the two-phase "
    "boiling region and increased the overall heat transfer coefficient. At "
    "the same power input, a higher flow rate provided better heat transfer "
    "performance."
)
VARIANTS = ("a", "b", "c")
CANONICAL_LAYOUT = "c"


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[tuple[str, set[str], dict[str, str | None]]] = []
        self.links: list[str] = []
        self.meta: list[dict[str, str | None]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        self.nodes.append((tag, classes, values))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "meta":
            self.meta.append(values)

    def handle_data(self, data: str) -> None:
        self.text.append(data)

    def matching(self, class_name: str):
        return [node for node in self.nodes if class_name in node[1]]

    def normalized_text(self) -> str:
        return " ".join(html.unescape(" ".join(self.text)).split())


def parse(path: Path) -> tuple[str, Page]:
    source = path.read_text(encoding="utf-8")
    page = Page()
    page.feed(source)
    return source, page


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    expected_links = {
        f"/facilities/falling-film-cooling-{variant}/" for variant in VARIANTS
    }
    for variant in VARIANTS:
        relative = f"facilities/falling-film-cooling-{variant}/index.html"
        path = SITE / relative
        require(path.is_file(), f"missing facility layout route: {relative}")
        if not path.is_file():
            continue
        source, page = parse(path)
        label = "/" + relative.removesuffix("index.html")
        robots = [
            (meta.get("content") or "").lower()
            for meta in page.meta
            if (meta.get("name") or "").lower() == "robots"
        ]
        require(any("noindex" in value for value in robots), f"{label}: missing noindex")
        require(len(page.matching("setup-study")) == 1,
                f"{label}: expected one setup-study")
        require(len(page.matching(f"setup-study--{CANONICAL_LAYOUT}")) == 1,
                f"{label}: expected canonical layout class")
        require(TITLE in page.normalized_text(), f"{label}: source title changed")
        require(DESCRIPTION in page.normalized_text(),
                f"{label}: Slide 2 wording is not verbatim")
        require(LEGACY_SLIDE not in source,
                f"{label}: complete slide is still displayed")
        require(len(page.matching("setup-study-figure")) == len(FIGURES),
                f"{label}: expected four extracted figures")
        for image, caption in FIGURES:
            require(source.count(f'src="{image}"') == 1,
                    f"{label}: extracted figure missing or duplicated: {image}")
            require(caption in page.normalized_text(),
                    f"{label}: source caption changed: {caption}")

    comparison_path = SITE / "facility-designs" / "index.html"
    require(comparison_path.is_file(), "missing facility design comparison route")
    if comparison_path.is_file():
        comparison_source, comparison = parse(comparison_path)
        found = {href for href in comparison.links if href in expected_links}
        require(found == expected_links,
                "facility comparison does not link exactly to layouts A/B/C")
        require(len(comparison.matching("facility-design-card--contain")) == 3,
                "facility comparison cards must preserve the complete diagram")
        require(comparison_source.count(f'src="{INDEX_IMAGE}"') == 3,
                "facility comparison cards do not use the cabinet diagram")
        robots = [
            (meta.get("content") or "").lower()
            for meta in comparison.meta
            if (meta.get("name") or "").lower() == "robots"
        ]
        require(any("noindex" in value for value in robots),
                "facility comparison route is missing noindex")

    facilities_path = SITE / "facilities" / "index.html"
    require(facilities_path.is_file(), "missing Facilities index")
    if facilities_path.is_file():
        source, page = parse(facilities_path)
        cards = [node for node in page.nodes if node[2].get("id") == FACILITY_ID]
        require(len(cards) == 1, "Facilities index must show one falling-film card")
        require(TITLE in page.normalized_text(), "Facilities card title changed")
        require(f'src="{INDEX_IMAGE}"' in source,
                "Facilities card does not use the cabinet diagram")
        require(len(page.matching("card-media-img--contain")) >= 1,
                "Facilities cards must include a complete diagram without cropping")
        require(LEGACY_SLIDE not in source,
                "Facilities card still displays the complete slide")

    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    require("facility-designs" not in sitemap,
            "temporary facility comparison leaked into sitemap.xml")
    for variant in VARIANTS:
        require(f"falling-film-cooling-{variant}" not in sitemap,
                f"temporary layout {variant.upper()} leaked into sitemap.xml")

    for path in SITE.rglob("*.html"):
        relative = path.relative_to(SITE).as_posix()
        if relative == "facility-designs/index.html":
            continue
        source = path.read_text(encoding="utf-8")
        require("/facility-designs/" not in source,
                f"{relative}: temporary comparison route is publicly linked")

    if failures:
        print("FACILITY LAYOUT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("FACILITY LAYOUT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
