#!/usr/bin/env python3
"""Audit the built site for public-content publication policy.

Run after Franklin.optimize(). This checks rendered behavior, not source text:
placeholder records/routes stay private, empty collections are honest and
noindexed, and hiding empty navigation never removes populated sections.
"""

from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
CANONICAL_FALLING_FILM_ROUTES = (
    "facilities/falling-film-cooling-system/index.html",
    "zh/facilities/falling-film-cooling-system/index.html",
)
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


def page(route: str) -> str:
    target = SITE / route.strip("/") / "index.html"
    if route == "/":
        target = SITE / "index.html"
    if not target.is_file():
        raise AssertionError(f"missing built page: {route} ({target})")
    return target.read_text(encoding="utf-8")


def rows(name: str, table: str) -> list[dict]:
    with (ROOT / "_data" / f"{name}.toml").open("rb") as handle:
        return tomllib.load(handle)[table]


def placeholder_tokens() -> set[str]:
    specs = (
        ("team", "person", ("id", "name_en", "name_zh", "topic_en", "topic_zh")),
        ("projects", "project", ("id", "title_en", "title_zh", "lead_en", "lead_zh")),
        ("news", "item", ("title_en", "title_zh", "body_en", "body_zh")),
        ("facilities", "item", ("id", "title_en", "title_zh", "lead_en", "lead_zh")),
    )
    tokens: set[str] = set()
    for name, table, fields in specs:
        for item in rows(name, table):
            if not item.get("placeholder", False):
                continue
            tokens.update(str(item.get(field, "")).strip() for field in fields)
    return {token for token in tokens if token}


def expect(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def attr_value(value: str) -> str:
    return rf'(?:"{re.escape(value)}"|{re.escape(value)})(?=[\s>])'


def has_noindex(html: str) -> bool:
    return bool(re.search(
        rf'<meta\b[^>]*\bname={attr_value("robots")}[^>]*'
        rf'\bcontent={attr_value("noindex,follow")}',
        html,
        re.IGNORECASE,
    ))


def has_data_value(html: str, name: str, value: str) -> bool:
    return bool(re.search(rf'\b{re.escape(name)}={attr_value(value)}', html))


def links(html: str) -> list[str]:
    matches = re.finditer(
        r'<a\b[^>]*\bhref=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', html, re.IGNORECASE,
    )
    return [next(value for value in match.groups() if value is not None) for match in matches]


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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not (SITE / "index.html").is_file():
        print("__site/ is not built. Run Franklin.optimize() first.")
        return 2

    failures: list[str] = []
    failures.extend(normalization_regression_failures())
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_paths = sitemap_routes(sitemap)
    for relative in PILOT_OUTPUTS:
        expect(not (SITE / relative).exists(),
               f"temporary pilot output remains published: /{relative}", failures)
        expect(normalize_internal_path("/" + relative) not in sitemap_paths,
               f"temporary pilot output remains in sitemap.xml: /{relative}", failures)
    for relative in CANONICAL_FALLING_FILM_ROUTES:
        expect((SITE / relative).is_file(),
               f"canonical falling-film route is missing: /{relative}", failures)
        expect(normalize_internal_path("/" + relative) in sitemap_paths,
               f"canonical falling-film route is missing from sitemap.xml: /{relative}", failures)
        route = "/" + relative.removesuffix("index.html")
        expect(not has_noindex(page(route)),
               f"canonical falling-film route must be indexable: {route}", failures)

    # /news/ and /zh/news/ used to be here. News has published items now, so
    # they are asserted as POPULATED below instead. The empty-state copy is
    # still in ui.toml and hfun_news_grid still returns it, for the day the
    # last item is withdrawn.
    empty_routes = {
        "/people/alumni/": ("alumni", "No alumni records are currently published."),
        "/zh/people/alumni/": ("alumni", "目前尚未公開歷屆成員資料。"),
    }
    for route, (kind, message) in empty_routes.items():
        html = page(route)
        expect(has_noindex(html), f"{route} is empty but is not noindex,follow", failures)
        expect(
            has_data_value(html, "data-empty-state", kind),
            f"{route} has no localized {kind} empty state",
            failures,
        )
        expect(message in html, f"{route} does not contain its localized empty-state copy", failures)

    for route in (
        "/people/", "/projects/", "/facilities/", "/news/",
        "/zh/people/", "/zh/projects/", "/zh/facilities/", "/zh/news/",
    ):
        expect(not has_noindex(page(route)), f"{route} has public records but is noindexed", failures)

    hidden_routes = []
    for item in rows("team", "person"):
        if item.get("placeholder", False):
            hidden_routes.extend((
                f'people/{item["id"]}/index.html',
                f'zh/people/{item["id"]}/index.html',
            ))
    for item in rows("projects", "project"):
        if item.get("placeholder", False):
            hidden_routes.extend((
                f'projects/{item["id"]}/index.html',
                f'zh/projects/{item["id"]}/index.html',
            ))
    # A news item's page is an ordinary .md file and does not know about the
    # placeholder flag. Withdraw the item and the card disappears from the
    # carousel and the grid while the article stays live at its own URL, findable
    # by anyone who has the link. Deleting the two pages is the other half of
    # withdrawing an item, and this is what says so.
    for item in rows("news", "item"):
        if item.get("placeholder", False):
            hidden_routes.extend((
                f'news/{item["id"]}/index.html',
                f'zh/news/{item["id"]}/index.html',
            ))
    for rel in hidden_routes:
        expect(not (SITE / rel).exists(), f"placeholder route was published: /{rel}", failures)

    forbidden = placeholder_tokens()
    for built in SITE.rglob("*.html"):
        html = built.read_text(encoding="utf-8")
        for href in links(html):
            expect(normalize_internal_path(href) not in PILOT_ROUTES,
                   f"{built.relative_to(SITE)} links to retired pilot route {href}", failures)
        for token in forbidden:
            expect(token not in html, f"{built.relative_to(SITE)} exposes {token!r}", failures)

    for route, expected_href in (
        ("/facilities/", "/facilities/falling-film-cooling-system/"),
        ("/zh/facilities/", "/zh/facilities/falling-film-cooling-system/"),
    ):
        expect(contains_exact_href(links(page(route)), expected_href),
               f"{route} is missing canonical facility link {expected_href}", failures)

    homes = (("/", ""), ("/zh/", "/zh"))
    for route, prefix in homes:
        html = page(route)
        # This used to assert the OPPOSITE, that the carousel was absent, because
        # every news item was a placeholder and the band rendered nothing. Real
        # items exist now, so an absent carousel is the fault worth catching.
        expect(has_data_value(html, "id", "newsSlider"), f"{route} lost the news carousel", failures)
        for visible in ("people", "projects", "facilities", "news"):
            href = f'href="{prefix}/{visible}/"'
            expect(href in html, f"{route} lost populated {visible} navigation", failures)
        alumni_href = f'href="{prefix}/people/alumni/"'
        expect(alumni_href not in html, f"{route} footer exposes empty alumni", failures)
        expect(
            "mailto:juliahsieh@nycu.edu.tw" not in html,
            f"{route} footer still exposes the removed contact column",
            failures,
        )

    people_empty_tiers = {
        "/people/": {
            "lead": ("Research leads", "Profiles will be added here."),
            "phd": ("PhD students", "Profiles will be added here."),
            "msc": ("MSc students", "Profiles will be added here."),
        },
        "/zh/people/": {
            "lead": ("研究主持群", "成員資料將於此處公布。"),
            "phd": ("博士班學生", "成員資料將於此處公布。"),
            "msc": ("碩士班學生", "成員資料將於此處公布。"),
        },
    }
    for route, tiers in people_empty_tiers.items():
        html = page(route)
        for tier, (heading, message) in tiers.items():
            expect(
                has_data_value(html, "data-empty-tier", tier),
                f"{route} does not render the empty {tier} section",
                failures,
            )
            expect(heading in html, f"{route} is missing the {heading!r} heading", failures)
            expect(message in html, f"{route} is missing localized temporary tier copy", failures)

    contact_pages = {
        "/contact/": ("Visit the laboratory", "Chair Professor", "Primary contact"),
        "/zh/contact/": ("參訪資訊", "講座教授", "主要聯絡人"),
    }
    for route, (visit_heading, title, retained_heading) in contact_pages.items():
        html = page(route)
        expect(visit_heading not in html, f"{route} still shows the visit section", failures)
        expect(title not in html, f"{route} still shows the removed professor title", failures)
        expect(retained_heading in html, f"{route} lost the primary contact details", failures)

    for route in ("/projects/", "/zh/projects/"):
        html = page(route)
        expect("placeholder-project" not in html, f"{route} lists the starter project", failures)
        expect("placeholder-phd-1" not in html, f"{route} exposes a placeholder researcher", failures)
        expect("Eiusmod Tempor" not in html, f"{route} names a placeholder researcher", failures)

    if failures:
        print("PUBLIC CONTENT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PUBLIC CONTENT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
