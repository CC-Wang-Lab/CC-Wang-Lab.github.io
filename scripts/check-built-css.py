#!/usr/bin/env python3
"""Check the stylesheet THE SITE ACTUALLY SERVES, not the one in _css/.

WHY THIS EXISTS, 2026-09-01.

A figure cap was written like this, and it was valid CSS:

    max-width: calc(var(--h-cap) * var(--sum-ar) + (var(--n) - 1) * var(--fig-gap));

`optimize()` minifies the stylesheet before deploying it, and the minifier
strips whitespace before an opening parenthesis. So the file on the live site
said:

    max-width:calc(var(--h-cap) * var(--sum-ar) +(var(--n) - 1) * var(--fig-gap))

In `calc()` the `+` and `-` operators must have whitespace on BOTH sides. That
expression is invalid, so `max-width` fell back to `none`, so every figure row
on the live site was uncapped. A photograph that was 438x640 on the local
preview was 1071x1566 online.

**Every other gate reads `_css/style.css`.** None of them could see this,
because the fault was not in the file they read. It was created afterwards, by
a tool, in the file nobody checked. That is the gap this closes.

Run it AFTER a build. In CI it runs after `optimize()`, which is the build that
minifies. Locally, `serve(single=true)` does not minify, so a local pass proves
the source is fine and proves nothing about the deployed file - build with
`optimize()` if you want the real answer.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS = ROOT / "__site" / "css" / "style.css"

# The four shapes a `+` or `-` cannot legally take inside calc(), and exactly
# the shapes a minifier creates when it removes whitespace around a bracket.
#
# Deliberately NOT a general "every operator needs spaces" test. Inside calc()
# a `-` is also the first character of every custom property (`--fig-gap`) and
# the sign of every negative literal (`-1px`), and a rule that tried to tell
# those apart would cry wolf. These four cannot be anything but a broken
# operator:
BROKEN = {
    "+(": "a plus hugging an opening bracket",
    "-(": "a minus hugging an opening bracket",
    ")+": "a plus hugging a closing bracket",
    ")-": "a minus hugging a closing bracket",
}


def calc_spans(css: str):
    """Every calc(...) in the file, with its start offset, brackets balanced."""
    for m in re.finditer(r"calc\(", css):
        depth = 0
        i = m.end() - 1
        while i < len(css):
            if css[i] == "(":
                depth += 1
            elif css[i] == ")":
                depth -= 1
                if depth == 0:
                    yield m.start(), css[m.start():i + 1]
                    break
            i += 1


def main() -> int:
    if not CSS.is_file():
        print("no built stylesheet at %s" % CSS.relative_to(ROOT))
        print("build the site first; in CI this runs after optimize()")
        return 1

    css = CSS.read_text(encoding="utf-8")
    minified = "\n" not in css.strip()[200:400] or css.count("\n") < 40
    failures = []

    for offset, span in calc_spans(css):
        for bad, why in BROKEN.items():
            if bad in span:
                line = css.count("\n", 0, offset) + 1
                failures.append(
                    "line %d: %s\n      %s" % (line, why, span[:160]))

    print("checked %d calc() expressions in %s"
          % (sum(1 for _ in calc_spans(css)), CSS.relative_to(ROOT)))
    if not minified:
        print("NOTE: this stylesheet is not minified, so it can only prove the")
        print("      SOURCE is sound. Build with optimize() for the real answer.")

    if failures:
        print("\n%d broken calc() expression(s):\n" % len(failures))
        for f in failures:
            print("  " + f)
        print("\nIn calc(), `+` and `-` must have whitespace on BOTH sides.")
        print("Rewrite so the operator is followed by a value, never a bracket:")
        print("  BAD   calc(var(--a) * var(--b) + (var(--n) - 1) * var(--gap))")
        print("  GOOD  calc(var(--a) * var(--b) + var(--gaps) * var(--gap))")
        print("`+ var(` and `- var(` both survive this minifier. `+ (` does not.")
        return 1

    print("every calc() survived minification intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
