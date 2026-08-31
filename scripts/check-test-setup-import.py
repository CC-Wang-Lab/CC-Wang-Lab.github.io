#!/usr/bin/env python3
"""Audit literal test-setup imports in data and the built Franklin site."""

from __future__ import annotations

import hashlib
import re
import sys
import tomllib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
SITEMAP = SITE / "sitemap.xml"
TEST_SETUP_ASSETS = ROOT / "_assets" / "img" / "test-setups"
SOURCE_DIRECTORY_MARKER = "CCWANG LAB Test Setup - Aug 2026"

# Recorded from the original 31-file source set during the full Task 12 audit.
# Keeping the manifest here makes later whole-slide checks independent of the
# user-specific source directory.
SOURCE_SLIDE_SHA256 = {
    "Slide1.jpg": "f15022513fe2d074739f2e617cbf83d092c76a0423a82a3c5df8d3e71d085dd7",
    "Slide2.jpg": "347f33d70bc9d650f1f358affcf6ac9158439b978d413280ef5c2e2ef56af1a8",
    "Slide3.jpg": "105555286644806bf06170124644c4402221dad8ab7fbfeb90d218484b83c49a",
    "Slide4.jpg": "6c34a2de57dfd871d292d124eeb7229ab22e12e296f72c30e858eda842dc4bfc",
    "Slide5.jpg": "0f90146f7a44623274adf05d11ae77359fc3bda5b8a92b03736c5709f1feb5d7",
    "Slide6.jpg": "2ddc252750309a962fd89f916896248b639492f075c330c618f8b0f6c87b9f76",
    "Slide7.jpg": "65ec71b085831a3ce8ad9164cd9b5650e31e437099c83e9e97ccb35c91306dff",
    "Slide8.jpg": "2c5055d7fb000c86822b963482ab5183d9fc36d277da9c4d9b327c98b6095aad",
    "Slide9.jpg": "a15e09587a5cc9ae0c63988f7bfcefa74739dcffc84f80e335a1a7c11dadef1a",
    "Slide10.jpg": "a095af0e0d0baf3e874c7a46a4134900c8fe5a4a835809c886437ead0d44ad77",
    "Slide11.jpg": "21b330dfe157c29f604b4abbd1a1eb0682afcb5df52ffd273b7ccdf3e874628e",
    "Slide12.jpg": "65dbf753ee74f4ef4c8ea757c6d207c4069ab1578dad6ff696747dfb46dc29a7",
    "Slide13.jpg": "262df83040d056cba33ef95ba07c07e8d4367a8f6676e257902c478c989a6b71",
    "Slide14.jpg": "21a9a0fe6ed54ae279369f8f0280c61e5118adb170d68301cbe54832795f03ae",
    "Slide15.jpg": "889c890a6bcd376b40ff20aace2c297f48e88f7e2de3e250a7d2fe6837e3051e",
    "Slide16.jpg": "9808585acd600ae2f0ea46564e39b7b13431c6a8225da409ca0cc9f61e3d30f7",
    "Slide17.jpg": "010b19b2fa277f98ae729e05b665f085d21a0f0bf744d1c2e365337355dad343",
    "Slide18.jpg": "1fe9ac68088b5b3a44db7d1fae0f21cfb733d4f3b0d860d5f4c3d561e2d4d34e",
    "Slide19.jpg": "307c627794555486e51dd808878b57820c13029ad4cd33c35a5c389bac6cc3f6",
    "Slide20.jpg": "4b48ef52a3dda6c4634c56ff42d659923ae650cd4e3edf43948a32e4557be457",
    "Slide21.jpg": "459cfa3e990296877cd5bba572012bed10a17148e638ffafa44d56c777dead10",
    "Slide22.jpg": "343a2894546b817403970f2f08130950ebb5cb7059a13e24275e32e6a35a187f",
    "Slide23.jpg": "058d6b2e0ae44afd780b511db35ebfc99c2fd8a57353e1cbe3bb5b00203365c2",
    "Slide24.jpg": "078ffec3000c43c06d63d563767b48d0230b875a38183febc53fee125c9a204a",
    "Slide25.jpg": "7c742483864674b3757496429d50419daede1a3635679dc2b057c3d6cb753f52",
    "Slide26.jpg": "3eaa047e62d2805151a762889ccb3f556474f67714ace9c2e9b9df5458bdffb1",
    "Slide27.jpg": "04c577c5084e24b89034e84ed640b38604f072abbf961d35559120196acd3732",
    "Slide28.jpg": "6884d69ea53a47f14d340dfe9b7224ab709882a736214b77d5e03c73eda216a6",
    "Slide29.jpg": "fe29eae639a2bdb30fd780b5d8e60d8ccada5cf66744563b5f0cf6b2bb82bdb8",
    "Slide30.jpg": "1c4eaba1ad9e7b4521eff1b8e13c591cfa9f1f01e3d5fdca1cadaa9f1d7a6182",
    "Slide31.jpg": "a12bf47895c47ed36e46c522cd97bcef8a6414cd7f77d7cfef9f1fd1c183e842",
}

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
        "immersion-cooling-microchannel-lid": ([19], "b", "electronics-cooling", 3),
        "oil-immersion-heat-transfer-enhancement": ([20], "c", "electronics-cooling", 5),
        "multi-agent-server-cooling-control": ([21, 22], "a", "ai-thermal", 5),
        "pulsating-jet-impingement": ([23], "b", "electronics-cooling", 2),
        "expansion-tank-pre-charge-pressure": ([24], "c", "hvacr", 4),
        "embedded-microfluidic-interlayer-cooling": ([25], "a", "electronics-cooling", 4),
        "supercritical-co2-chiller": ([26], "b", "hvacr", 2),
        "thermosyphon-working-fluid-filling-ratio": ([27], "c", "two-phase", 1),
    },
}

PLURAL = {"facility": "facilities", "project": "projects"}
EXPECTED_COUNTS = {"facility": 14, "project": 12}
EXPECTED_LAYOUTS = {
    "facility": {"a": 5, "b": 4, "c": 5},
    "project": {"a": 4, "b": 4, "c": 4},
}

# The equipment lines lost their hand-typed "1. " and "2. " on 2026-08-31.
# render_setup_sections wraps every item in a <ul>, so the browser was already
# numbering them and the reader saw "1. 1. SMC chiller". The words are
# unchanged; only the duplicated ordinal is gone.
REQUIRED_PROJECT_HTML_TEXT = {
    "supercritical-co2-chiller": (
        "This test facility is used to (1) performance evaluation of CO₂ (2) provide a test cold plate system having 15 kW capacity and applicable for multiple cold plate system to examine mal-distribution issues for 2-phase cold plates subject uneven heat loading.",
        "This study primarily investigates the design of a 10 kW single-phase cold plate system using a CO₂-based chiller in conjunction with a single-phase fluorinated fluid, with the aim of testing and understanding the heat transfer capabilities of CO₂ in its supercritical state.",
        "Status: Under Construction",
        "SMC chiller (HRZC010-WS)",
        "20 kW air-cooled coil (Custom-made by Icherng)",
        "CO₂ refrigerant, Galden HT-135 fluorinated fluid",
    ),
    "thermosyphon-working-fluid-filling-ratio": (
        "This ongoing study investigates the effects of working fluid and filling ratio on the cooling performance of a two-phase thermosyphon heat sink. Heating power, evaporator and condenser temperature distributions, thermal resistance, and parameters related to high-power chip cooling in data centers are evaluated to determine the optimal filling ratio for each fluid and establish recommended filling-ratio ranges.",
        "Status: In progress",
        "R-1233zd(E), R-601, and acetone",
        "Thermal test vehicle, six DC power supplies, data logger, T-type thermocouples, and pressure gauge",
    ),
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.classes: list[set[str]] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, _tag: str, attrs) -> None:
        values = dict(attrs)
        self.classes.append(set((values.get("class") or "").split()))

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    sitemap = SITEMAP.read_text(encoding="utf-8") if SITEMAP.is_file() else ""

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(SITEMAP.is_file(), "missing built sitemap: __site/sitemap.xml")

    expected_slide_names = {f"Slide{number}.jpg" for number in range(1, 32)}
    require(set(SOURCE_SLIDE_SHA256) == expected_slide_names,
            "source-slide hash manifest must contain exactly Slide1.jpg through Slide31.jpg")
    require(len(set(SOURCE_SLIDE_SHA256.values())) == 31,
            "source-slide hash manifest must contain 31 unique hashes")
    require(all(re.fullmatch(r"[0-9a-f]{64}", digest)
                for digest in SOURCE_SLIDE_SHA256.values()),
            "source-slide hash manifest contains an invalid SHA-256 digest")

    source_hashes = {
        digest: filename for filename, digest in SOURCE_SLIDE_SHA256.items()
    }
    require(TEST_SETUP_ASSETS.is_dir(),
            "missing test-setup asset directory: _assets/img/test-setups")
    if TEST_SETUP_ASSETS.is_dir():
        for asset in sorted(path for path in TEST_SETUP_ASSETS.rglob("*")
                            if path.is_file()):
            digest = sha256_file(asset)
            source_filename = source_hashes.get(digest)
            require(source_filename is None,
                    f"{asset.relative_to(ROOT)} is a byte-identical complete source slide "
                    f"({source_filename})")

    if SITE.is_dir():
        for path in sorted(SITE.rglob("*.html")):
            html = path.read_text(encoding="utf-8")
            relative = path.relative_to(ROOT)
            require(re.search(r"Slide[^/\\\"']*\.jpg", html, re.IGNORECASE) is None,
                    f"{relative}: generated HTML references a source Slide*.jpg")
            require(SOURCE_DIRECTORY_MARKER.casefold() not in html.casefold(),
                    f"{relative}: generated HTML exposes the source-directory text")
            require("{{" not in html and "}}" not in html,
                    f"{relative}: generated HTML contains an unresolved template marker")

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
                visible_text = " ".join(" ".join(page.text_parts).split())
                for fact_index, fragment in enumerate(
                        REQUIRED_PROJECT_HTML_TEXT.get(record_id, ()), start=1):
                    require(fragment in visible_text,
                            f"{route}: missing selectable source fact {fact_index}")
    if failures:
        print("TEST SETUP IMPORT AUDIT FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("TEST SETUP IMPORT AUDIT CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
