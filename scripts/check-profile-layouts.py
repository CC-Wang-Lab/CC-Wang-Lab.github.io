#!/usr/bin/env python3
"""Audit the built profile-variant contract without mutating ``__site``."""

from __future__ import annotations

import re
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
LAYOUTS = ("editorial", "dossier", "narrative")


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
            "profile-identity",
            "profile-narrative",
            "profile-record",
            "profile-switcher",
        ):
            require(
                len(page.matching(class_name)) == 1,
                f"{label}: expected one .{class_name}",
            )
        choices = page.matching("profile-layout-choice")
        require(len(choices) == 3, f"{label}: expected three profile choices")
        require(
            {node[2].get("data-profile-layout-choice") for node in choices}
            == set(LAYOUTS),
            f"{label}: choices are not the exact allowlist",
        )
        switchers = page.matching("profile-switcher")
        require(
            bool(switchers) and "hidden" not in switchers[0][2],
            f"{label}: three-mode profile switcher must be visible by default",
        )
        order = [
            page.first_index("pi-heading"),
            page.first_index("profile-identity"),
            page.first_index("profile-narrative"),
            page.first_index("profile-record"),
        ]
        require(
            min(order) >= 0 and order == sorted(order),
            f"{label}: DOM order must be name, identity, narrative, facts",
        )
        require(
            any("profile-layout.js" in (script.get("src") or "") for script in page.scripts),
            f"{label}: profile-layout.js is not loaded",
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
        require(
            "data-profile-layout-compare" in html and all(value in html for value in LAYOUTS),
            f"{label}: pre-paint query allowlist is missing",
        )
        init_at = html.find("data-profile-layout-compare")
        style_at = html.find("/css/style.css")
        require(
            0 <= init_at < style_at,
            f"{label}: profile layout is not selected before the stylesheet",
        )
        source_path = ROOT / (relative.removesuffix("/index.html") + ".md")
        source = source_path.read_text(encoding="utf-8")
        require(
            "col-lg-4" not in source and "col-lg-8" not in source,
            f"{label}: legacy two-column profile wrappers remain",
        )

    comparison_pages = {
        "profile-designs/index.html": "/people/",
        "zh/profile-designs/index.html": "/zh/people/",
    }
    for relative, profile_prefix in comparison_pages.items():
        path = SITE / relative
        require(path.is_file(), f"missing comparison page: {relative}")
        if not path.is_file():
            continue
        html, page = parse(path)
        require(len(page.matching("page-hd")) == 1, f"{relative}: page header is not rendered")
        require("&lt;header" not in html, f"{relative}: page header HTML is escaped as text")
        robots = [
            (meta.get("content") or "").lower()
            for meta in page.meta
            if (meta.get("name") or "").lower() == "robots"
        ]
        require(any("noindex" in value for value in robots), f"{relative}: missing noindex")
        require('role="list"' not in html and "role=list " not in html,
                f"{relative}: comparison links use a list role without listitems")
        expected = {
            f"{profile_prefix}{person}/?profile-layout={layout}"
            for person in ("cc-wang", "maysam-gholampour")
            for layout in LAYOUTS
        }
        found = {href for href in page.links if "profile-layout=" in href}
        require(found == expected, f"{relative}: comparison links differ from the six expected URLs")

    for path in SITE.rglob("*.html"):
        relative = path.relative_to(SITE).as_posix()
        if relative in comparison_pages:
            continue
        html = path.read_text(encoding="utf-8")
        require("/profile-designs/" not in html, f"{relative}: comparison page is publicly linked")
        require("/zh/profile-designs/" not in html, f"{relative}: Chinese comparison page is publicly linked")

    home = (SITE / "index.html").read_text(encoding="utf-8")
    require("data-profile-layout-compare" not in home,
            "profile pre-paint controller leaked onto a non-profile page")
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    require("profile-designs" not in sitemap,
            "temporary comparison routes leaked into sitemap.xml")

    for relative in ("docs/templates/person.en.md", "docs/templates/person.zh.md"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in (
            "@@profile-layout",
            "@@profile-identity",
            "@@profile-narrative,prose",
            "@@profile-record",
            "{{profile_switcher}}",
        ):
            require(marker in source, f"{relative}: future profile template lacks {marker}")
        require("col-lg-4" not in source and "col-lg-8" not in source,
                f"{relative}: future profile template still uses the legacy layout")

    controller = ROOT / "_assets" / "js" / "profile-layout.js"
    require(controller.is_file(), "missing _assets/js/profile-layout.js")
    if controller.is_file():
        source = controller.read_text(encoding="utf-8")
        require(all(re.search(rf"[\"']{value}[\"']", source) for value in LAYOUTS),
                "profile-layout.js does not contain the exact allowlist")
        require("history.replaceState" in source, "profile switcher does not update the URL")
        require(".lang-switch" in source,
                "profile controller does not preserve the layout on language links")
        require("switcher.hidden = false" in source,
                "profile controller does not keep the three-mode selector visible")
        require("switcher.hidden = !value" not in source,
                "profile controller still hides the selector without a query value")
        require("localStorage" not in source and "sessionStorage" not in source,
                "profile layout choice must not persist")

    css = (ROOT / "_css" / "style.css").read_text(encoding="utf-8")
    for selector in (
        '[data-profile-layout="editorial"]',
        '[data-profile-layout="dossier"]',
        '[data-profile-layout="narrative"]',
    ):
        require(selector in css, f"missing CSS layout state {selector}")
    for declaration in (
        "font-size: var(--fs-3xl)",
        "font-size: var(--fs-2xl)",
        "font-size: var(--fs-4xl)",
        "font-size: var(--fs-lg)",
        "font-size: var(--fs-xl)",
        "font-size: var(--fs-md)",
    ):
        require(declaration in css, f"profile type contract is missing `{declaration}`")

    if failures:
        print("PROFILE LAYOUT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PROFILE LAYOUT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
