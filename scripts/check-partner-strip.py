#!/usr/bin/env python3
"""Audit the built sponsor-logo and arrowless interaction contract."""

from __future__ import annotations

import re
import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"


class PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[tuple[str, set[str], dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        self.nodes.append((tag, set((values.get("class") or "").split()), values))

    def matching(self, class_name: str):
        return [node for node in self.nodes if class_name in node[1]]


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

    for relative in ("index.html", "zh/index.html"):
        html, page = parse(SITE / relative)
        require(not page.matching("pt-arrow"), f"{relative}: visible/invisible partner arrows remain")
        viewports = page.matching("pt-viewport")
        require(len(viewports) == 2, f"{relative}: expected exactly two partner row controls")
        ids = {node[2].get("id") for node in page.nodes if node[2].get("id")}
        names: set[str | None] = set()
        for _, _, attrs in viewports:
            names.add(attrs.get("aria-label"))
            require(attrs.get("tabindex") == "0", f"{relative}: partner row is not tabbable")
            require(attrs.get("role") == "group", f"{relative}: partner row lacks group semantics")
            require(bool(attrs.get("aria-label")), f"{relative}: partner row has no accessible name")
            require(attrs.get("aria-describedby") in ids,
                    f"{relative}: partner row instructions are missing")
            require(attrs.get("aria-keyshortcuts") == "ArrowLeft ArrowRight",
                    f"{relative}: partner row does not expose both arrow shortcuts")
        require(len(names) == 2 and None not in names,
                f"{relative}: the two partner rows need distinct localized names")

        rows = page.matching("pt-row")
        require(len(rows) == 4, f"{relative}: expected an original and duplicate list per row")
        if len(rows) == 4:
            require(rows[0][2].get("aria-hidden") is None and
                    rows[1][2].get("aria-hidden") == "true" and
                    rows[2][2].get("aria-hidden") is None and
                    rows[3][2].get("aria-hidden") == "true",
                    f"{relative}: only duplicate logo lists may be aria-hidden")

        logos = page.matching("pt-logo")
        frames = page.matching("pt-logo-frame")
        require(len(logos) > 0, f"{relative}: sponsor SVG logos are missing")
        require(not frames, f"{relative}: sponsor logo frames were not reverted")
        for tag, _, attrs in logos:
            require(tag == "img" and attrs.get("draggable") == "false",
                    f"{relative}: logo images must not start native image dragging")
        require("filter:" not in html.lower(), f"{relative}: inline logo filtering remains")

    ui = tomllib.loads((ROOT / "_data" / "ui.toml").read_text(encoding="utf-8"))
    partners = ui.get("partners", {})
    for key in (
        "row_one_en", "row_one_zh", "row_two_en", "row_two_zh",
        "instructions_en", "instructions_zh",
    ):
        require(bool(partners.get(key)), f"ui.toml: missing localized partner label {key}")

    css = (ROOT / "_css" / "style.css").read_text(encoding="utf-8")
    require(".pt-logo-frame" not in css, "style.css: sponsor logo frame styling remains")
    require(".pt-arrow" not in css, "style.css: arrow styling remains")
    require("filter: grayscale(1);" in css,
            "style.css: default grayscale sponsor treatment was not restored")
    require("filter: grayscale(0);" in css,
            "style.css: sponsor hover color treatment was not restored")
    require("filter: grayscale(1) invert(1) brightness(1.6);" in css,
            "style.css: previous dark-theme sponsor treatment was not restored")
    require("filter: grayscale(0) invert(0);" in css,
            "style.css: previous dark-theme sponsor hover treatment was not restored")
    focus_rule = re.search(r"\.pt-viewport:focus-visible\s*\{([^{}]*)\}", css)
    require(bool(focus_rule) and re.search(r"outline\s*:\s*(0|none)", focus_rule.group(1)),
            "style.css: partner focus must not draw a rectangular outline")
    cue_rule = re.search(
        r"\.pt-band:has\(\.pt-viewport:focus-visible\)::after\s*\{([^{}]*)\}", css
    )
    require(bool(cue_rule) and "background:" in cue_rule.group(1),
            "style.css: keyboard focus needs a non-rectangular line cue")
    require("@media (forced-colors: active)" in css,
            "style.css: partner focus needs a forced-colors fallback")

    generator = (ROOT / "utils.jl").read_text(encoding="utf-8")
    require("pt-arrow" not in generator, "utils.jl: partner arrow markup remains")
    for attribute in ("tabindex=\"0\"", "aria-keyshortcuts=\"ArrowLeft ArrowRight\"",
                      "aria-describedby", "draggable=\"false\""):
        require(attribute in generator, f"utils.jl: partner markup lacks {attribute}")
    require("pt-logo-frame" not in generator, "utils.jl: sponsor logo frame markup remains")

    controller = (ROOT / "_assets" / "js" / "partners.js").read_text(encoding="utf-8")
    for obsolete in (".pt-prev", ".pt-next"):
        require(obsolete not in controller, f"partners.js: obsolete handler {obsolete} remains")
    for required in (
        'addEventListener("keydown"', '"ArrowLeft"', '"ArrowRight"',
        'addEventListener("pointerdown"', 'addEventListener("pointermove"',
        'addEventListener("pointercancel"', 'addEventListener("lostpointercapture"',
        "setPointerCapture", "releasePointerCapture", "window.LabMotion",
    ):
        require(required in controller, f"partners.js: missing {required}")
    require("if (e.button !== 0) return;" in controller,
            "partners.js: non-primary mouse/pen buttons are not rejected")
    require("if (!view.hasPointerCapture(e.pointerId)) return;" in controller,
            "partners.js: failed pointer capture can leave a row dragging")
    require(controller.find("setPointerCapture") < controller.find("b.dragging = true"),
            "partners.js: drag state starts before pointer capture succeeds")
    require("view.focus(" not in controller,
            "partners.js: pointer drag must not force a focus rectangle")
    require("if (moving && !b.dragging)" in controller and
            "b.baseTime = performance.now();" in controller,
            "partners.js: automatic movement must resume after drag release")

    if failures:
        print("PARTNER STRIP AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PARTNER STRIP AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
