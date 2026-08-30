#!/usr/bin/env python3
"""Audit the built D-only profile contract without mutating ``__site``."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
PROFILE_PATHS = (
    "people/cc-wang/index.html",
    "people/maysam-gholampour/index.html",
    "zh/people/cc-wang/index.html",
    "zh/people/maysam-gholampour/index.html",
)
class PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[tuple[str, set[str], dict[str, str | None]]] = []
        self.links: list[str] = []
        self.head_links: list[dict[str, str | None]] = []
        self.meta: list[dict[str, str | None]] = []
        self.scripts: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        self.nodes.append((tag, classes, values))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "link":
            self.head_links.append(values)
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "script":
            self.scripts.append(values)

    def matching(self, class_name: str):
        return [node for node in self.nodes if class_name in node[1]]

    def first_index(self, class_name: str) -> int:
        return next(
            (index for index, node in enumerate(self.nodes) if class_name in node[1]),
            -1,
        )


def parse(path: Path) -> tuple[str, PageAudit]:
    html = path.read_text(encoding="utf-8")
    audit = PageAudit()
    audit.feed(html)
    return html, audit


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for relative in PROFILE_PATHS:
        path = SITE / relative
        require(path.is_file(), f"missing built profile: {relative}")
        if not path.is_file():
            continue
        html, page = parse(path)
        label = "/" + relative.removesuffix("index.html")
        for class_name in (
            "profile-layout",
            "profile-narrative",
            "profile-record",
            "profile-header-identity",
        ):
            require(
                len(page.matching(class_name)) == 1,
                f"{label}: expected one .{class_name}",
            )
        require(not page.matching("profile-identity"),
                f"{label}: duplicate body identity remains")
        require(not page.matching("profile-switcher"),
                f"{label}: profile design switcher remains")
        require(not page.matching("profile-layout-choice"),
                f"{label}: profile design choices remain")
        header_order = [
            page.first_index("pi-heading"),
            page.first_index("profile-header-identity"),
            page.first_index("profile-narrative"),
            page.first_index("profile-record"),
        ]
        require(
            min(header_order) >= 0 and header_order == sorted(header_order),
            f"{label}: DOM order must be name, header identity, narrative, facts",
        )
        require(
            not any("profile-layout.js" in (script.get("src") or "") for script in page.scripts),
            f"{label}: retired profile-layout.js is still loaded",
        )
        expected_canonical = "https://cc-wang-lab.github.io/" + relative.removesuffix("index.html")
        canonicals = [
            link.get("href")
            for link in page.head_links
            if (link.get("rel") or "").lower() == "canonical"
        ]
        require(
            canonicals == [expected_canonical],
            f"{label}: expected one clean canonical URL {expected_canonical}",
        )
        require("data-profile-layout" not in html,
                f"{label}: retired layout-state attributes remain")
        source_path = ROOT / (relative.removesuffix("/index.html") + ".md")
        source = source_path.read_text(encoding="utf-8")
        require(
            "col-lg-4" not in source and "col-lg-8" not in source,
            f"{label}: legacy two-column profile wrappers remain",
        )

    comparison_pages = (
        "profile-designs/index.html",
        "zh/profile-designs/index.html",
    )
    for relative in comparison_pages:
        require(not (SITE / relative).exists(),
                f"retired comparison route is still generated: {relative}")

    for path in SITE.rglob("*.html"):
        relative = path.relative_to(SITE).as_posix()
        html = path.read_text(encoding="utf-8")
        require("/profile-designs/" not in html, f"{relative}: comparison page is publicly linked")
        require("/zh/profile-designs/" not in html, f"{relative}: Chinese comparison page is publicly linked")
        require("profile-layout=" not in html,
                f"{relative}: retired profile-layout query is still emitted")

    home = (SITE / "index.html").read_text(encoding="utf-8")
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    require("profile-designs" not in sitemap,
            "temporary comparison routes leaked into sitemap.xml")

    for relative in ("docs/templates/person.en.md", "docs/templates/person.zh.md"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in (
            "@@profile-layout",
            "@@profile-narrative,prose",
            "@@profile-record",
            "{{person_header}}",
        ):
            require(marker in source, f"{relative}: future profile template lacks {marker}")
        require("@@profile-identity" not in source,
                f"{relative}: future profile template retains duplicate identity")
        require("{{profile_switcher}}" not in source,
                f"{relative}: future profile template retains design switcher")
        require("col-lg-4" not in source and "col-lg-8" not in source,
                f"{relative}: future profile template still uses the legacy layout")

    controller = ROOT / "_assets" / "js" / "profile-layout.js"
    require(not controller.exists(), "retired _assets/js/profile-layout.js remains live")

    css = (ROOT / "_css" / "style.css").read_text(encoding="utf-8")
    require("[data-profile-layout=" not in css,
            "retired conditional profile layouts remain in CSS")
    require(".profile-switcher" not in css,
            "retired profile switcher styling remains in CSS")

    if failures:
        print("PROFILE LAYOUT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PROFILE LAYOUT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
