#!/usr/bin/env python3
"""
Reads the colour tokens out of _css/style.css and checks every foreground /
background pair the site actually renders, in BOTH themes, against WCAG 2.2 AA.

Why this exists: the brand colours are sampled from the lab logo, and a logo
colour is not a text colour. --lab-orange is 2.58:1 on the light page and
--lab-blue is 4.20:1, so neither may carry text in light mode. Eleven rules used
to do exactly that. This script is what stops it coming back.

Run from the repo root:   python scripts/check-contrast.py
Exit code 0 means every pair passes. Standard library only.
"""
import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parent.parent / "_css" / "style.css"

# WCAG 2.2 thresholds
AA_TEXT = 4.5   # 1.4.3 normal text
AA_UI = 3.0     # 1.4.11 non-text contrast: control borders, focus rings, icons


def srgb_to_linear(channel):
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.2126 * srgb_to_linear(r)
            + 0.7152 * srgb_to_linear(g)
            + 0.0722 * srgb_to_linear(b))


def ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def over(fg_rgb, alpha, bg_hex):
    """Composite a partly transparent colour onto an opaque one."""
    b = bg_hex.lstrip("#")
    return "#" + "".join(
        "%02x" % round(c * alpha + int(b[i * 2:i * 2 + 2], 16) * (1 - alpha))
        for i, c in enumerate(fg_rgb)
    )


def read_tokens():
    """Pull every custom property out of the stylesheet, comments stripped."""
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)
    # This reader has no brace-depth awareness, which is fine only while no
    # colour token is redefined inside a media query. Check that, rather than
    # assume it: a token overridden at one width would otherwise be asserted at
    # the base value and pass at every width.
    for block in re.findall(r"@media[^{]*\{(.*?)\n\}", text, re.S):
        stray = re.findall(r"(--(?:lab|bs|on)-[a-z0-9-]*(?:color|bg|accent|"
                           r"muted|surface|danger|border|dark|brand|orange|"
                           r"blue|ink)[a-z0-9-]*)\s*:", block)
        if stray:
            raise SystemExit("colour token(s) defined inside a @media block, "
                             "which this reader cannot resolve: "
                             + ", ".join(sorted(set(stray))))
    blocks = {}
    for selector, body in re.findall(r"([^{}]*?)\{([^{}]*?)\}", text, re.S):
        sel = " ".join(selector.split())
        if "--" not in body:
            continue
        if "data-bs-theme=" in sel and "dark" in sel:
            key = "dark"
        elif ":root" in sel:
            key = "light"
        else:
            continue
        for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", body):
            blocks.setdefault(key, {})[name] = value.strip()
    # Bare :root carries the light theme AND the shared tokens, so dark
    # inherits from it and then overrides.
    dark = dict(blocks.get("light", {}))
    dark.update(blocks.get("dark", {}))
    return {"light": blocks.get("light", {}), "dark": dark}


def resolve(tokens, name, seen=()):
    """Follow var(--x) chains down to a literal hex."""
    value = tokens[name]
    m = re.match(r"^var\((--[a-z0-9-]+)\)$", value)
    if m:
        if m.group(1) in seen:
            raise ValueError("circular token: " + name)
        return resolve(tokens, m.group(1), seen + (name,))
    return value


# (label, foreground token, background token or None for the icon tile, threshold)
PAIRS = [
    ("body text on the page",         "--bs-body-color",     "--bs-body-bg",        AA_TEXT),
    ("body text on a card",           "--bs-body-color",     "--lab-surface",       AA_TEXT),
    ("body text on the alt band",     "--bs-body-color",     "--lab-surface-2",     AA_TEXT),
    ("heading",                       "--bs-emphasis-color", "--bs-body-bg",        AA_TEXT),
    ("muted on the page",             "--lab-muted",         "--bs-body-bg",        AA_TEXT),
    ("muted on a card",               "--lab-muted",         "--lab-surface",       AA_TEXT),
    ("muted on the alt band",         "--lab-muted",         "--lab-surface-2",     AA_TEXT),
    ("link on the page",              "--lab-accent",        "--bs-body-bg",        AA_TEXT),
    ("link on a card",                "--lab-accent",        "--lab-surface",       AA_TEXT),
    ("link on the alt band",          "--lab-accent",        "--lab-surface-2",     AA_TEXT),
    ("link hover on the page",        "--lab-accent-hover",  "--bs-body-bg",        AA_TEXT),
    ("link hover on the alt band",    "--lab-accent-hover",  "--lab-surface-2",     AA_TEXT),
    ("blue accent on the page",       "--lab-accent-2",      "--bs-body-bg",        AA_TEXT),
    ("blue accent on a card",         "--lab-accent-2",      "--lab-surface",       AA_TEXT),
    ("blue accent on the alt band",   "--lab-accent-2",      "--lab-surface-2",     AA_TEXT),
    ("error message",                 "--lab-danger",        "--bs-body-bg",        AA_TEXT),
    ("error on a card",               "--lab-danger",        "--lab-surface",       AA_TEXT),
    ("text on the brand fill",        "--lab-on-brand",      "--lab-orange",        AA_TEXT),
    ("text on the bright brand fill", "--lab-on-brand",      "--lab-orange-bright", AA_TEXT),
    ("form border on a card",         "--lab-border-strong", "--lab-surface",       AA_UI),
    ("form border on the page",       "--lab-border-strong", "--bs-body-bg",        AA_UI),
    ("focus ring on the page",        "--lab-accent",        "--bs-body-bg",        AA_UI),
    ("focus ring on a card",          "--lab-accent",        "--lab-surface",       AA_UI),
    ("card-icon glyph on its tile",   "--lab-accent",        None,                  AA_UI),
]

# The always-dark regions ignore the theme. These are the four opaque grounds
# they use: the hero ground, the numbers band, and the two CTA gradient stops.
#
# NOT modelled here, on purpose: text sitting over the hero VIDEO. The frame
# behind it changes, so no static number is honest. .hero-title, .hero-lead and
# .hero-caption all carry a text-shadow for exactly that reason, and they are
# judged from the screenshots instead.
DARK_GROUNDS = {
    "the hero ground":      "#0b0b12",
    "the ink band":         "#181828",
    "the CTA gradient":     "#232344",
    "the CTA gradient end": "#2c3f56",
}

# (token, bar, what it is). --on-dark-3 appears TWICE because it does two jobs:
# it is the text colour of .hero-caption, .ns-head, .ns-date, .ns-nav-item and
# .typed-lead, and it is the border of .hero .btn-ghost and .motion-toggle. Text
# is held to 4.5 and a component border to 3.0.
ON_DARK = [
    ("--on-dark-1", AA_TEXT, "text"),
    ("--on-dark-2", AA_TEXT, "text"),
    ("--on-dark-3", AA_TEXT, "text"),
    ("--on-dark-3", AA_UI, "border"),
]

# The tile behind .card-icon is a wash of the brand orange over the card.
ICON_TILE = {"light": ((216, 144, 48), 0.14, "--lab-surface"),
             "dark":  ((237, 164, 63), 0.16, "--lab-surface")}


def main():
    themes = read_tokens()
    failures = []
    for theme in ("light", "dark"):
        tk = themes[theme]
        print("\n=== %s ===" % theme.upper())
        for label, fg, bg, need in PAIRS:
            f = resolve(tk, fg)
            if bg is None:
                rgb, alpha, under = ICON_TILE[theme]
                b = over(rgb, alpha, resolve(tk, under))
            else:
                b = resolve(tk, bg)
            r = ratio(f, b)
            ok = r >= need
            print("  %-32s %-7s on %-7s %5.2f  need %.1f  %s"
                  % (label, f, b, r, need, "pass" if ok else "FAIL"))
            if not ok:
                failures.append("%s: %s is %.2f, needs %.1f" % (theme, label, r, need))

    print("\n=== ALWAYS-DARK REGIONS (theme-independent) ===")
    tk = themes["light"]
    for token, need, role in ON_DARK:
        alpha = float(re.search(r"([0-9.]+)\)\s*$", tk[token]).group(1))
        worst, worst_ground = 99.0, ""
        for name, ground in DARK_GROUNDS.items():
            r = ratio(over((255, 255, 255), alpha, ground), ground)
            if r < worst:
                worst, worst_ground = r, name
        ok = worst >= need
        print("  %-12s as %-6s alpha %.2f  worst %5.2f on %-22s need %.1f  %s"
              % (token, role, alpha, worst, worst_ground, need,
                 "pass" if ok else "FAIL"))
        if not ok:
            failures.append("%s as %s is %.2f on %s, needs %.1f"
                            % (token, role, worst, worst_ground, need))

    print()
    if failures:
        print("%d FAILURE(S):" % len(failures))
        for f in failures:
            print("  -", f)
        return 1
    print("every pair passes WCAG 2.2 AA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
