#!/usr/bin/env python3
"""Audit the canonical shared setup renderer in the built Franklin site."""

from __future__ import annotations

import sys
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
CSS_SOURCE = ROOT / "_css" / "style.css"
EXPECTED = {
    "id": "falling-film-cooling-system",
    "layout": "c",
    "routes": (
        "facilities/falling-film-cooling-system/index.html",
        "zh/facilities/falling-film-cooling-system/index.html",
    ),
    "figures": (
        "/assets/img/facilities/falling-film-cooling-100w.jpg",
        "/assets/img/facilities/falling-film-cooling-500w.jpg",
        "/assets/img/facilities/falling-film-cooling-cabinet.png",
        "/assets/img/facilities/falling-film-cooling-dimensions.png",
    ),
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[tuple[str, set[str], dict[str, str | None]]] = []
        self.links: list[str] = []
        self.meta: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        self.nodes.append((tag, classes, values))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "meta":
            self.meta.append(values)

    def matching(self, class_name: str):
        return [node for node in self.nodes if class_name in node[1]]

    def has_noindex(self) -> bool:
        return any(
            (meta.get("name") or "").lower() == "robots"
            and "noindex" in (meta.get("content") or "").lower()
            for meta in self.meta
        )


def parse(path: Path) -> tuple[str, Page]:
    source = path.read_text(encoding="utf-8")
    page = Page()
    page.feed(source)
    return source, page


def css_rule(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css, re.DOTALL)
    return match.group(1) if match else ""


def renderer_contract_failures() -> list[str]:
    failures: list[str] = []
    css = CSS_SOURCE.read_text(encoding="utf-8")
    if "--measure: 74ch;" not in css:
        failures.append("CSS must define --measure as the 74ch narrative width")
    if "max-width: var(--measure);" not in css_rule(css, ".setup-study-copy"):
        failures.append("shared setup-study copy must cap narrative width at --measure")

    section_cases = (
        (
            "localized",
            'include("utils.jl"); locvar(::Symbol) = "zh"; '
            'render_setup_sections(Dict{String, Any}("section" => '
            'Any[Dict{String, Any}("items_en" => Any["valid"], '
            '"items_zh" => Any["   "])]))',
        ),
        (
            "fallback",
            'include("utils.jl"); locvar(::Symbol) = "zh"; '
            'render_setup_sections(Dict{String, Any}("section" => '
            'Any[Dict{String, Any}("items_en" => Any["   "])]))',
        ),
    )
    for label, code in section_cases:
        result = subprocess.run(
            ["julia", "--project=.", "-e", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0 or "blank" not in output.lower():
            failures.append(f"{label} blank section item must fail renderer validation")
    return failures


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    failures.extend(renderer_contract_failures())
    canonical_href = f"/facilities/{EXPECTED['id']}/"
    sitemap_path = SITE / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.is_file() else ""

    for relative in EXPECTED["routes"]:
        path = SITE / relative
        route = "/" + relative.removesuffix("index.html")
        require(path.is_file(), f"missing canonical setup route: {relative}")
        if not path.is_file():
            continue
        source, page = parse(path)
        require(len(page.matching("setup-study")) == 1,
                f"{route}: expected one setup-study")
        require(len(page.matching(f"setup-study--{EXPECTED['layout']}")) == 1,
                f"{route}: expected setup-study--{EXPECTED['layout']}")
        require(len(page.matching("setup-study-figure")) == len(EXPECTED["figures"]),
                f"{route}: expected four setup-study figures")
        for figure in EXPECTED["figures"]:
            require(source.count(f'src="{figure}"') == 1,
                    f"{route}: figure missing or duplicated: {figure}")
        require(not page.has_noindex(), f"{route}: must be indexable")
        require(relative.replace("/", "\\") in sitemap,
                f"{route}: canonical setup route missing from sitemap.xml")

    for relative, expected_href in (
        ("facilities/index.html", canonical_href),
        ("zh/facilities/index.html", f"/zh{canonical_href}"),
    ):
        path = SITE / relative
        require(path.is_file(), f"missing facilities listing route: {relative}")
        if path.is_file():
            _, page = parse(path)
            require(expected_href in page.links,
                    f"/{relative.removesuffix('index.html')}: missing canonical facility link {expected_href}")

    if failures:
        print("SETUP RENDERER AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SETUP RENDERER AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
