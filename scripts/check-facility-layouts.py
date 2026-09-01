#!/usr/bin/env python3
"""Audit the canonical falling-film facility and reject retired pilot routes."""

from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


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
# The page composes itself now, so what is asserted is that the four
# extracted figures are on it and each sits in a justified row.
CANONICAL_ROWS = 2
CANONICAL_ROUTES = (
    "facilities/falling-film-cooling-system/index.html",
    "zh/facilities/falling-film-cooling-system/index.html",
)
PILOT_OUTPUTS = (
    "facility-designs/index.html",
    *(f"facilities/falling-film-cooling-{variant}/index.html" for variant in VARIANTS),
)
PILOT_ROUTES = (
    "/facility-designs/",
    *(f"/facilities/falling-film-cooling-{variant}/" for variant in VARIANTS),
)


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


def normalized_origin(value: str) -> tuple[str, str, int] | None:
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if (scheme not in ("http", "https") or not hostname or
            parts.username is not None or parts.password is not None):
        return None
    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    if not 1 <= effective_port <= 65535:
        return None
    return scheme, hostname.lower(), effective_port


def configured_site_origin() -> tuple[str, str, int]:
    config = (ROOT / "config.md").read_text(encoding="utf-8")
    match = re.search(r'^website_url\s*=\s*"([^"]+)"', config, re.MULTILINE)
    if match is None:
        raise RuntimeError("config.md must define website_url")
    origin = normalized_origin(match.group(1))
    if origin is None:
        raise RuntimeError("config.md website_url must be an absolute http(s) URL")
    return origin


CANONICAL_ORIGIN = configured_site_origin()


def contains_exact_href(hrefs, expected: str) -> bool:
    return expected in hrefs


def normalize_internal_path(value: str) -> str | None:
    parts = urlsplit(value.replace("\\", "/"))
    if parts.scheme or parts.netloc or not parts.path.startswith("/"):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if segments and segments[-1] == "index.html":
        segments.pop()
    return "/" + "/".join(segments) + ("/" if segments else "")


def sitemap_routes(sitemap: str) -> set[str]:
    routes: set[str] = set()
    for loc in re.findall(r"<loc>(.*?)</loc>", sitemap, re.DOTALL):
        normalized_loc = loc.replace("\\", "/")
        try:
            parts = urlsplit(normalized_loc)
        except ValueError:
            continue
        if parts.scheme:
            if normalized_origin(normalized_loc) != CANONICAL_ORIGIN:
                continue
        elif parts.netloc:
            continue
        route = normalize_internal_path(parts.path)
        if route is not None:
            routes.add(route)
    return routes


def normalization_regression_failures() -> list[str]:
    failures: list[str] = []
    cases = (
        ("missing trailing slash", "/facility-designs", "/facility-designs/"),
        ("index output", "/facilities/falling-film-cooling-a/index.html", "/facilities/falling-film-cooling-a/"),
        ("query and fragment", "/facilities/falling-film-cooling-b/?draft=1#figures", "/facilities/falling-film-cooling-b/"),
    )
    for label, raw, expected in cases:
        if normalize_internal_path(raw) != expected:
            failures.append(f"path normalization regression: {label}")
    canonical = "/facilities/falling-film-cooling-system/"
    if contains_exact_href((canonical + "index.html", canonical + "?source=slide"), canonical):
        failures.append("exact canonical link regression: normalized variant accepted")
    if not contains_exact_href((canonical,), canonical):
        failures.append("exact canonical link regression: exact href rejected")
    sitemap = "<loc>https://cc-wang-lab.github.io\\facilities\\falling-film-cooling-c\\index.html</loc>"
    if "/facilities/falling-film-cooling-c/" not in sitemap_routes(sitemap):
        failures.append("path normalization regression: Windows sitemap output")
    external = "<loc>https://evil.example/facilities/falling-film-cooling-system/index.html</loc><loc>https://evil.example/facilities/falling-film-cooling-a/index.html</loc>"
    if sitemap_routes(external):
        failures.append("sitemap origin regression: external authority was treated as internal")
    configured = normalized_origin("https://cc-wang-lab.github.io/")
    if normalized_origin("https://CC-WANG-LAB.GITHUB.IO:443/facilities/falling-film-cooling-c/index.html") != configured:
        failures.append("sitemap origin regression: HTTPS default port or host case was rejected")
    if normalized_origin("http://example.test/") != normalized_origin("http://EXAMPLE.TEST:80/"):
        failures.append("sitemap origin regression: HTTP default port or host case was rejected")
    if normalized_origin("https://user@cc-wang-lab.github.io/") is not None:
        failures.append("sitemap origin regression: userinfo was accepted")
    if normalized_origin("https://cc-wang-lab.github.io:bad/") is not None:
        failures.append("sitemap origin regression: invalid port was accepted")
    matching = "<loc>https://CC-WANG-LAB.GITHUB.IO:443\\facilities\\falling-film-cooling-c\\index.html</loc>"
    if "/facilities/falling-film-cooling-c/" not in sitemap_routes(matching):
        failures.append("sitemap origin regression: configured HTTPS default port was rejected")
    rejected = "<loc>https://cc-wang-lab.github.io:444/facilities/falling-film-cooling-system/index.html</loc><loc>http://cc-wang-lab.github.io/facilities/falling-film-cooling-a/index.html</loc><loc>https://evil.example/facilities/falling-film-cooling-b/index.html</loc>"
    if sitemap_routes(rejected):
        failures.append("sitemap origin regression: wrong port, scheme, or host was accepted")
    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(normalization_regression_failures())

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for relative in CANONICAL_ROUTES:
        path = SITE / relative
        require(path.is_file(), f"missing canonical facility route: {relative}")
        if not path.is_file():
            continue
        source, page = parse(path)
        label = "/" + relative.removesuffix("index.html")
        robots = [
            (meta.get("content") or "").lower()
            for meta in page.meta
            if (meta.get("name") or "").lower() == "robots"
        ]
        require(not any("noindex" in value for value in robots), f"{label}: must be indexable")
        require(len(page.matching("setup-rows")) == 1,
                f"{label}: expected one composed setup-rows block")
        require(len(page.matching("fig-row")) == CANONICAL_ROWS,
                f"{label}: expected {CANONICAL_ROWS} justified rows")
        require(TITLE in page.normalized_text(), f"{label}: source title changed")
        require(DESCRIPTION in page.normalized_text(),
                f"{label}: Slide 2 wording is not verbatim")
        require(LEGACY_SLIDE not in source,
                f"{label}: complete slide is still displayed")
        require(len(page.matching("fig ")) + len(page.matching("fig")) >= len(FIGURES),
                f"{label}: expected four extracted figures")
        for image, caption in FIGURES:
            require(source.count(f'src="{image}"') == 1,
                    f"{label}: extracted figure missing or duplicated: {image}")
            require(caption in page.normalized_text(),
                    f"{label}: source caption changed: {caption}")

    for relative in PILOT_OUTPUTS:
        require(not (SITE / relative).exists(),
                f"temporary pilot output remains published: {relative}")

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

    for relative, expected_href in (
        ("facilities/index.html", "/facilities/falling-film-cooling-system/"),
        ("zh/facilities/index.html", "/zh/facilities/falling-film-cooling-system/"),
    ):
        path = SITE / relative
        require(path.is_file(), f"missing facilities listing route: {relative}")
        if path.is_file():
            _, page = parse(path)
            require(contains_exact_href(page.links, expected_href),
                    f"/{relative.removesuffix('index.html')}: missing canonical facility link {expected_href}")

    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_paths = sitemap_routes(sitemap)
    for relative in PILOT_OUTPUTS:
        require(normalize_internal_path("/" + relative) not in sitemap_paths,
                f"temporary pilot output remains in sitemap.xml: {relative}")
    for relative in CANONICAL_ROUTES:
        require(normalize_internal_path("/" + relative) in sitemap_paths,
                f"canonical facility route is missing from sitemap.xml: {relative}")

    for path in SITE.rglob("*.html"):
        _, page = parse(path)
        for href in page.links:
            route = normalize_internal_path(href)
            require(route not in PILOT_ROUTES,
                    f"{path.relative_to(SITE).as_posix()}: temporary pilot route is linked: {href}")

    if failures:
        print("FACILITY LAYOUT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("FACILITY LAYOUT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
