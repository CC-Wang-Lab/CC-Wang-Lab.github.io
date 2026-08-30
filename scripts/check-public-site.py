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


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"


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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not (SITE / "index.html").is_file():
        print("__site/ is not built. Run Franklin.optimize() first.")
        return 2

    failures: list[str] = []
    empty_routes = {
        "/news/": ("news", "No laboratory news is currently available."),
        "/facilities/": ("facilities", "Facility records have not yet been published."),
        "/people/alumni/": ("alumni", "No alumni records are currently published."),
        "/zh/news/": ("news", "目前尚無實驗室最新消息。"),
        "/zh/facilities/": ("facilities", "實驗設備資料尚未公開。"),
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

    for route in ("/people/", "/projects/", "/zh/people/", "/zh/projects/"):
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
    for rel in hidden_routes:
        expect(not (SITE / rel).exists(), f"placeholder route was published: /{rel}", failures)

    forbidden = placeholder_tokens()
    for built in SITE.rglob("*.html"):
        html = built.read_text(encoding="utf-8")
        for token in forbidden:
            expect(token not in html, f"{built.relative_to(SITE)} exposes {token!r}", failures)

    homes = (("/", ""), ("/zh/", "/zh"))
    for route, prefix in homes:
        html = page(route)
        expect(not has_data_value(html, "id", "newsSlider"), f"{route} exposes placeholder news", failures)
        for hidden in ("news",):
            href = f'href="{prefix}/{hidden}/"'
            expect(href not in html, f"{route} navigation exposes empty {hidden}", failures)
        for visible in ("people", "projects", "facilities"):
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

    for route in ("/projects/porous-pool-boiling/", "/zh/projects/porous-pool-boiling/"):
        html = page(route)
        expect("Eiusmod Tempor" not in html, f"{route} names a placeholder researcher", failures)
        expect("艾尤斯莫 坦波" not in html, f"{route} names a placeholder researcher", failures)

    if failures:
        print("PUBLIC CONTENT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PUBLIC CONTENT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
