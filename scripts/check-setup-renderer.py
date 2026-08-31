#!/usr/bin/env python3
"""Audit the canonical shared setup renderer in the built Franklin site."""

from __future__ import annotations

import sys
import re
import subprocess
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
CSS_SOURCE = ROOT / "_css" / "style.css"
EXPECTED = {
    "id": "falling-film-cooling-system",
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
PILOT_OUTPUTS = (
    "facility-designs/index.html",
    "facilities/falling-film-cooling-a/index.html",
    "facilities/falling-film-cooling-b/index.html",
    "facilities/falling-film-cooling-c/index.html",
)
PILOT_ROUTES = (
    "/facility-designs/",
    "/facilities/falling-film-cooling-a/",
    "/facilities/falling-film-cooling-b/",
    "/facilities/falling-film-cooling-c/",
)
CARVERA_ROUTES = (
    "facilities/carvera-desktop-cnc/index.html",
    "zh/facilities/carvera-desktop-cnc/index.html",
)
CARVERA_SOURCE_URL = "https://www.kidentech.com/carvera"
CARVERA_SOURCE_LABEL = "Link to detailed information:"
PROJECT_EXPECTED = {
    "id": "gaming-laptop-hybrid-vapor-chamber",
    "routes": (
        "projects/gaming-laptop-hybrid-vapor-chamber/index.html",
        "zh/projects/gaming-laptop-hybrid-vapor-chamber/index.html",
    ),
    "figures": (
        "/assets/img/test-setups/gaming-laptop-hybrid-vapor-chamber/upper-experimental-system.jpg",
        "/assets/img/test-setups/gaming-laptop-hybrid-vapor-chamber/lower-experimental-system.jpg",
    ),
    "title": "Hybrid Vapor Chamber–Heat Pipe Module for Thermal Management of Gaming Laptops",
    "body": (
        "This experimental system evaluates an additively manufactured hybrid "
        "vapor chamber–heat pipe module for the thermal management of gaming "
        "laptops. Heat is transferred from the heating block to the test specimen "
        "and then conducted through the heat pipes to the fins on both sides. "
        "Forced-convection cooling is provided by airflow conditioned through a "
        "wind tunnel. An infrared thermal camera positioned below the specimen "
        "measures the surface temperature distribution to evaluate temperature "
        "uniformity and heat transfer performance."
    ),
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[tuple[str, set[str], dict[str, str | None]]] = []
        self.links: list[str] = []
        self.anchors: list[tuple[str, str]] = []
        self.meta: list[dict[str, str | None]] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        self.nodes.append((tag, classes, values))
        if tag == "a" and values.get("href"):
            href = str(values["href"])
            self.links.append(href)
            self._anchor_href = href
            self._anchor_text = []
        elif tag == "meta":
            self.meta.append(values)

    def handle_data(self, data: str) -> None:
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href is not None:
            self.anchors.append((self._anchor_href, "".join(self._anchor_text)))
            self._anchor_href = None
            self._anchor_text = []

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


def css_rule(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css, re.DOTALL)
    return match.group(1) if match else ""


def julia_result(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["julia", "--project=.", "-e", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def studentless_project_literal() -> str:
    return (
        'Dict{String, Any}("id" => "studentless-test", '
        '"area" => "electronics-cooling", '
        '"image" => "/assets/img/projects/placeholder.svg", '
        '"title_en" => "Studentless project", '
        '"title_zh" => "Studentless project", '
        '"lead_en" => "Studentless project lead", '
        '"lead_zh" => "Studentless project lead")'
    )


def renderer_contract_failures() -> list[str]:
    failures: list[str] = []
    css = CSS_SOURCE.read_text(encoding="utf-8")
    # Comments are stripped before every rule below. Each of these rules is
    # explained in the stylesheet in words that contain the very thing being
    # searched for, and the first version of this check failed on its own
    # explanation three separate times.
    def rule(selector):
        return re.sub(r"/\*.*?\*/", "", css_rule(css, selector), flags=re.S)

    # 1. The notes FILL THE ROW, and the measure is held by columns.
    #
    # This assertion has been rewritten three times, so the history is worth
    # keeping. Each version was right about its own layout:
    #
    #   - under layouts a and c the notes sat in a grid column already
    #     narrower than a measure, so a cap could never bind, and the check
    #     forbade one;
    #   - under layout b the notes WERE the container, and a cap left the
    #     right half of the row empty, measured at 700px inside 1320px;
    #   - under rows a cap left the top of the page half empty above a
    #     full-width row of pictures, which reads as a missing cell.
    #
    # So the block fills the row and `column-width` holds the line length
    # instead. A max-width would put the empty half back, and a bare
    # full-width block runs to about 160 characters a line.
    notes = rule(".setup-notes")
    if re.search(r"max-width\s*:\s*(?!none)", notes):
        failures.append("the setup notes must fill their row; a max-width leaves "
                        "the page half empty above a full-width row of pictures")
    if not re.search(r"column-width\s*:\s*[\d.]+rem", notes):
        failures.append("the setup notes need a column-width to hold the measure; "
                        "without one the line runs to about 160 characters at 1440")
    if "overflow-wrap: break-word;" not in notes:
        failures.append("the setup notes must break a long word; "
                        "TUNNEL+Environmental pushed the page 82px wider than a "
                        "320px screen")

    # 2. A row is justified by ASPECT RATIO, and capped on the row.
    #
    # `flex: calc(--ar-w / --ar-h) 1 0` with a zero basis is the whole of the
    # justification: free space is shared in proportion to aspect, so every
    # picture in the row lands at the same height. A basis other than 0 breaks
    # it silently, and the row still looks plausible.
    figure = rule(".fig")
    if "calc(var(--ar-w) / var(--ar-h))" not in figure:
        failures.append("a figure must take its flex-grow from its aspect ratio, "
                        "or the row is no longer justified")
    if not re.search(r"flex:[^;]*\b1 0\b", figure):
        failures.append("a figure must have flex-basis 0; any other basis stops "
                        "the widths coming out proportional to aspect")
    row = rule(".fig-row")
    if "max-width: calc(" not in row or "--sum-ar" not in row:
        failures.append("the row height cap must be applied to the ROW's max-width; "
                        "a max-height on the image letterboxes it instead")
    media = rule(".fig-media")
    if "max-width: var(--nat-w)" not in media:
        failures.append("a figure must never be painted wider than its own pixels; "
                        ".fig-media needs max-width: var(--nat-w)")

    # 3. Nothing may be placed by a literal figure id, ever again. Four ids
    # were hard-coded in the stylesheet and only one record in the site carried
    # them, so 25 of 26 records fell through into a track built for a different
    # record and every gate stayed green.
    for dead in ("--cabinet", "--dimensions", "--100w", "--500w"):
        if f".setup-study-figure{dead}" in css or f".fig{dead}" in css:
            failures.append(f"figure placement keyed on the literal id '{dead}' is "
                            "back; placement must follow the data, not an id")

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
        result = julia_result(code)
        output = result.stdout + result.stderr
        if result.returncode == 0 or "blank" not in output.lower():
            failures.append(f"{label} blank section item must fail renderer validation")

    typed_item_code = (
        'include("utils.jl"); locvar(::Symbol) = "en"; '
        'print(render_setup_sections(Dict{String, Any}("section" => '
        'Any[Dict{String, Any}("items_en" => Any['
        '"<em>ordinary</em>", Dict{String, Any}('
        '"type" => "source-url", "label_en" => "Source:", '
        '"value" => "https://example.com/source")])])))'
    )
    result = julia_result(typed_item_code)
    output = result.stdout + result.stderr
    if result.returncode != 0:
        failures.append("typed source-URL section item must render successfully")
    else:
        if "<li>&lt;em&gt;ordinary&lt;/em&gt;</li>" not in output:
            failures.append("ordinary section items must remain escaped text")
        expected_anchor = (
            '<li>Source: <a href="https://example.com/source">'
            'https://example.com/source</a></li>'
        )
        if expected_anchor not in output:
            failures.append("typed source-URL section item must render a safe anchor")

    studentless = studentless_project_literal()
    optional_cases = (
        (
            "project card",
            'include("utils.jl"); locvar(::Symbol) = "en"; '
            f"print(project_card({studentless}))",
            "card-by",
        ),
        (
            "project header",
            'include("utils.jl"); '
            'locvar(name::Symbol) = name == :project ? "studentless-test" : "en"; '
            f"fixture = {studentless}; projects() = Any[fixture]; "
            "print(hfun_project_header())",
            "project-by",
        ),
        (
            "person-profile project filtering",
            'include("utils.jl"); '
            'locvar(name::Symbol) = name == :person ? "maysam-gholampour" : "en"; '
            f"fixture = {studentless}; projects() = Any[fixture]; "
            "print(hfun_person_facts())",
            "studentless-test",
        ),
    )
    for label, code, forbidden in optional_cases:
        result = julia_result(code)
        output = result.stdout + result.stderr
        if result.returncode != 0:
            failures.append(f"omitted student must not break {label}: {output.strip()}")
        elif forbidden in output:
            failures.append(f"omitted student must not emit {forbidden} in {label}")

    invalid_id = "explicit-invalid-student-id"
    invalid_code = (
        'include("utils.jl"); locvar(::Symbol) = "en"; '
        f'fixture = {studentless}; fixture["student"] = "{invalid_id}"; '
        "print(project_card(fixture))"
    )
    result = julia_result(invalid_code)
    output = result.stdout + result.stderr
    if result.returncode == 0 or invalid_id not in output:
        failures.append("an explicit invalid student id must still fail through person_by_id")

    # The positive case, on a SYNTHETIC row rather than a real project. The
    # project that used to supply it was one of the two test pages deleted on
    # 2026-08-31. After that the only row carrying a `student` is the
    # placeholder, which is never published, so a fixture keeps the coverage
    # without pinning it to a page that may or may not exist.
    with_student = studentless_project_literal().replace(
        '"lead_zh" => "Studentless project lead")',
        '"lead_zh" => "Studentless project lead", "student" => "maysam-gholampour")')
    present_code = (
        'include("utils.jl"); locvar(::Symbol) = "en"; '
        f"print(project_card({with_student}))"
    )
    result = julia_result(present_code)
    output = result.stdout + result.stderr
    if result.returncode != 0 or 'class="card-by"' not in output or "Maysam Gholampour" not in output:
        failures.append("a project WITH a student must still render its byline: "
                        + output.strip()[:200])
    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(normalization_regression_failures())

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    failures.extend(renderer_contract_failures())
    with (ROOT / "_data" / "projects.toml").open("rb") as handle:
        project_data = tomllib.load(handle)
    project_hits = [
        project
        for project in project_data.get("project", [])
        if project.get("id") == PROJECT_EXPECTED["id"]
    ]
    require(len(project_hits) == 1,
            f"expected one project record for {PROJECT_EXPECTED['id']}")
    if project_hits:
        project = project_hits[0]
        require("student" not in project,
                "imported Slide 3 project must omit student rather than infer a byline")
        require("layout" not in project,
                "imported Slide 3 project must not carry a layout key; "
                "layouts a, b and c are retired and each page composes itself")
        require(project.get("source_slides") == [3],
                "imported Slide 3 project must cite source_slides = [3]")
        require(project.get("title_en") == PROJECT_EXPECTED["title"] and
                project.get("title_zh") == PROJECT_EXPECTED["title"],
                "imported Slide 3 project title must preserve and mirror the exact source")
        require(project.get("body_en") == PROJECT_EXPECTED["body"] and
                project.get("body_zh") == PROJECT_EXPECTED["body"],
                "imported Slide 3 project body must preserve and mirror the exact source")
        require(tuple(figure.get("image") for figure in project.get("figure", [])) ==
                PROJECT_EXPECTED["figures"],
                "imported Slide 3 project must contain exactly the upper and lower photographs")
        card_code = (
            'include("utils.jl"); locvar(::Symbol) = "en"; '
            f'fixture = only(filter(p -> p["id"] == "{PROJECT_EXPECTED["id"]}", projects())); '
            "print(project_card(fixture))"
        )
        result = julia_result(card_code)
        output = result.stdout + result.stderr
        require(result.returncode == 0,
                "imported Slide 3 project card must render without a student")
        require('class="card-by"' not in output,
                "imported Slide 3 project card must omit .card-by")
    canonical_href = f"/facilities/{EXPECTED['id']}/"
    sitemap_path = SITE / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.is_file() else ""
    sitemap_paths = sitemap_routes(sitemap)

    for relative in PILOT_OUTPUTS:
        require(not (SITE / relative).exists(),
                f"temporary pilot output remains published: {relative}")
        require(normalize_internal_path("/" + relative) not in sitemap_paths,
                f"temporary pilot output remains in sitemap.xml: {relative}")

    for path in SITE.rglob("*.html"):
        _, page = parse(path)
        for href in page.links:
            route = normalize_internal_path(href)
            require(route not in PILOT_ROUTES,
                    f"{path.relative_to(SITE).as_posix()}: temporary pilot route is linked: {href}")

    for relative in EXPECTED["routes"]:
        path = SITE / relative
        route = "/" + relative.removesuffix("index.html")
        require(path.is_file(), f"missing canonical setup route: {relative}")
        if not path.is_file():
            continue
        source, page = parse(path)
        require(len(page.matching("setup-rows")) == 1,
                f"{route}: expected one composed setup-rows block")
        require(len(page.matching("fig-row")) >= 1,
                f"{route}: expected at least one justified figure row")
        require(source.count('class="fig fig--') == len(EXPECTED["figures"]),
                f"{route}: expected four figures")
        for figure in EXPECTED["figures"]:
            require(source.count(f'src="{figure}"') == 1,
                    f"{route}: figure missing or duplicated: {figure}")
        require(not page.has_noindex(), f"{route}: must be indexable")
        require(normalize_internal_path("/" + relative) in sitemap_paths,
                f"{route}: canonical setup route missing from sitemap.xml")

    for relative, expected_href in (
        ("facilities/index.html", canonical_href),
        ("zh/facilities/index.html", f"/zh{canonical_href}"),
    ):
        path = SITE / relative
        require(path.is_file(), f"missing facilities listing route: {relative}")
        if path.is_file():
            _, page = parse(path)
            require(contains_exact_href(page.links, expected_href),
                    f"/{relative.removesuffix('index.html')}: missing canonical facility link {expected_href}")

    for relative in CARVERA_ROUTES:
        path = SITE / relative
        route = "/" + relative.removesuffix("index.html")
        require(path.is_file(), f"missing Carvera setup route: {relative}")
        if path.is_file():
            source, page = parse(path)
            require(CARVERA_SOURCE_LABEL in source,
                    f"{route}: missing exact source-URL label")
            require(
                (CARVERA_SOURCE_URL, CARVERA_SOURCE_URL) in page.anchors,
                f"{route}: source URL must be an anchor with exact href and visible text",
            )

    for relative in PROJECT_EXPECTED["routes"]:
        path = SITE / relative
        route = "/" + relative.removesuffix("index.html")
        require(path.is_file(), f"missing imported project route: {relative}")
        if not path.is_file():
            continue
        source, page = parse(path)
        require(len(page.matching("setup-rows")) == 1,
                f"{route}: expected one composed setup-rows block")
        require(not page.matching("project-by"),
                f"{route}: studentless imported project must omit .project-by")
        require(source.count('class="fig fig--') == 2,
                f"{route}: expected exactly two figures")
        for figure in PROJECT_EXPECTED["figures"]:
            require(source.count(f'src="{figure}"') == 1,
                    f"{route}: figure missing or duplicated: {figure}")

    if failures:
        print("SETUP RENDERER AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SETUP RENDERER AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
