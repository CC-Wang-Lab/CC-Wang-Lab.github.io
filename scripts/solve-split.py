#!/usr/bin/env python3
"""
Solves the two column widths of every `split:` block and writes them to _data/.

    python scripts/solve-split.py                 # report only, writes nothing
    python scripts/solve-split.py --write         # write split_en / split_zh
    python scripts/solve-split.py --write --only gaming-laptop-hybrid-vapor-chamber

A detail page may put its words beside its pictures:

    blocks = [ "split:upper-experimental-system lower-experimental-system" ]

The two columns should end at the same height. This finds the two widths that
make them, by measuring the real page in a real browser.

WHY IT CANNOT BE COMPUTED IN JULIA AT BUILD TIME
------------------------------------------------
The obvious formula is `ceil(N * c / w) * L`: characters, over column width,
times line height. It is wrong on two thirds of these records.

  - The words are not one paragraph. A record carries an <h2> at 37.6px over a
    41.36px line with a 40px top margin, and list items that occupy one line
    each whatever the column width. multi-agent-server-cooling-control holds
    196 characters in twelve list items, and its height moves from 805px to
    722px across the whole plausible range of widths. No formula in N sees it.
  - The pictures are capped. `--h-cap: min(--fig-max-h, --nat-h)` holds nine of
    the rows to 640px however wide their column gets, and a <figcaption> adds
    25 to 42px that re-wraps as the column narrows.

So both heights are read off the browser's own layout and the answer is stored.

THE STORED NUMBER IS A COPY OF A FACT AND CAN GO STALE
------------------------------------------------------
Edit a sentence in _data/ and the words change height, and the stored split is
then wrong. Nothing here guards that, and nothing needs to: a stale split IS a
pair of columns that no longer end level, which is exactly what
`shoot.py --measure` checks on every detail page at every width. One mechanism,
not two. It cannot run in CI, which has no browser, so run the sweep locally
before a merge.

ONE VALUE PER LANGUAGE
----------------------
`split_en` and `split_zh` are solved separately and are identical today, because
every record's Chinese prose is still a copy of its English. The day a native
speaker writes the Chinese, they will not be: Chinese sets far more compactly,
and a split solved on English would stop ending level on the Chinese page, where
only a Chinese reader would ever see it.
"""
from __future__ import annotations

import argparse
import base64  # noqa: F401  (cdp imports cleanly only with the stdlib it wants)
import functools
import http.server
import json
import re
import socketserver
import sys
import threading
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cdp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
PORT = 8129
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

# The width every split is solved at. 1400px is the first viewport at which the
# container reaches its full 1320px, giving 1296px of content, and it is the
# range the stylesheet applies the solved widths in. Below it the block falls
# back to the 5/7 proportion.
VIEWPORT = 1440
CONTENT = 1296.0

# The measure band, in characters a line. 55 is the floor the site owner chose
# after seeing 45 and 55 rendered side by side: 45 is only the width below which
# justified text opens rivers, which is a lower bar than reading well.
CH_LO, CH_HI = 55, 75
# The pictures should not shrink far inside their own column. A target, not a
# cliff: a record a little under it is a judgement for a person, not a failure.
FILL_TARGET = 0.60
# One line height. The words step by whole lines, so nothing can beat this.
TOLERANCE = 29.76

PROBE = r"""
(function (LO, HI, STEP) {
  var block = document.querySelector(".setup-split");
  if (!block) return { error: "no .setup-split on this page" };
  var words = block.querySelector(".setup-split-words");
  var row = block.querySelector(".fig-row");
  if (!words || !row) return { error: "split is missing a child" };

  var rows = document.querySelector(".setup-rows");
  var rcs = getComputedStyle(rows);
  var content = rows.getBoundingClientRect().width
                - parseFloat(rcs.paddingLeft) - parseFloat(rcs.paddingRight);
  var gap = parseFloat(getComputedStyle(block).columnGap);

  /* The average character width of this record's own body text, in its own
     font. NOT the `ch` unit: `ch` is the width of a zero, and ET Book's zero
     is 9.39px where its average character is 7.90px, so `ch` would report a
     column 19%% narrower in characters than it really is. */
  var para = words.querySelector("p") || words.querySelector("li");
  var avgChar = null;
  if (para) {
    var pcs = getComputedStyle(para);
    var text = (words.textContent || "").replace(/\s+/g, " ").trim();
    var probe = document.createElement("span");
    probe.style.cssText = "position:absolute;left:-99999px;top:0;white-space:pre;";
    probe.style.fontFamily = pcs.fontFamily; probe.style.fontSize = pcs.fontSize;
    probe.style.fontWeight = pcs.fontWeight; probe.style.fontStyle = pcs.fontStyle;
    probe.style.letterSpacing = pcs.letterSpacing;
    probe.textContent = text.slice(0, 600);
    document.body.appendChild(probe);
    avgChar = probe.getBoundingClientRect().width / probe.textContent.length;
    document.body.removeChild(probe);
  }

  /* Both curves, measured. Set a width, force layout, read the height back.
     The row keeps its own max-width throughout, so --h-cap and the no-upscale
     rule act exactly as they would in a real column. */
  function sweep(el, keepMax) {
    var savedW = el.style.width, savedMax = el.style.maxWidth,
        savedFlex = el.style.flex;
    el.style.flex = "0 0 auto";
    if (!keepMax) el.style.maxWidth = "none";
    var out = [];
    for (var w = LO; w <= HI; w += STEP) {
      el.style.width = w + "px";
      void el.offsetHeight;
      out.push([w, +el.getBoundingClientRect().height.toFixed(2)]);
    }
    el.style.width = savedW; el.style.maxWidth = savedMax;
    el.style.flex = savedFlex;
    void el.offsetHeight;
    return out;
  }

  return {
    content: +content.toFixed(2), gap: +gap.toFixed(2),
    avgChar: avgChar ? +avgChar.toFixed(4) : null,
    chars: (words.textContent || "").replace(/\s+/g, " ").trim().length,
    wordsCurve: sweep(words, false),
    rowCurve: sweep(row, true)
  };
})(%d, %d, %d)
"""


def records():
    """Every record whose page composes a `split:` block, with its routes."""
    out = []
    for name, key, base, page_dir in (
            ("facilities.toml", "item", "/facilities/", "facilities"),
            ("projects.toml", "project", "/projects/", "projects")):
        with open(ROOT / "_data" / name, "rb") as fh:
            rows = tomllib.load(fh)[key]
        for row in rows:
            if row.get("placeholder", False):
                continue
            page = ROOT / page_dir / (row["id"] + ".md")
            if not page.is_file():
                continue
            if not re.search(r'"\s*split[(:]', page.read_text(encoding="utf-8")):
                continue
            out.append({"id": row["id"], "file": name, "key": key,
                        "routes": {"en": base + row["id"] + "/",
                                   "zh": "/zh" + base + row["id"] + "/"}})
    return out


def solve(m):
    """The two widths, from one page's measured curves. See the module docstring."""
    if m.get("error"):
        return {"error": m["error"]}
    c = m["avgChar"]
    if not c:
        return {"error": "no body text to measure a character width from"}
    K = m["content"] - m["gap"]
    words = dict((w, h) for w, h in m["wordsCurve"])
    step = m["wordsCurve"][1][0] - m["wordsCurve"][0][0]

    def row_width_for(h):
        """Widest the row can be while staying no taller than h."""
        best_w = best_err = None
        for w, rh in m["rowCurve"]:
            if rh > h + 0.5:
                continue
            err = h - rh
            if best_err is None or err < best_err:
                best_err, best_w = err, w
        return best_w, best_err

    ok = []
    w = round(max(min(words), CH_LO * c) / step) * step
    while w <= min(max(words), CH_HI * c):
        h = words.get(w)
        if h is not None:
            track = K - w
            need, err = row_width_for(h)
            if need is not None and need <= track + 0.5 and err <= TOLERANCE:
                ok.append((w, h, need, track - need, err, need / track))
        w += step
    if not ok:
        return {"error": "no width in %d..%d characters balances this record"
                         % (CH_LO, CH_HI), "chars": m["chars"]}
    # The largest pictures a readable measure allows: smallest spare width.
    w, h, need, slack, err, fill = min(ok, key=lambda t: t[3])
    return {"words": int(round(w)), "pics": int(round(need)),
            "cpl": round(w / c, 1), "H": round(h, 1), "err": round(err, 2),
            "fill": round(fill, 3), "chars": m["chars"],
            "thin": fill < FILL_TARGET}


def write_split(file_name, key, rec_id, en, zh):
    """Replace or insert `split_en` / `split_zh` on one record, in place.

    Text patching, not a TOML round-trip, and deliberately: tomli-w would
    reorder every key and drop every comment in a 2,700-line file that is
    edited by hand by lab members.
    """
    path = ROOT / "_data" / file_name
    text = path.read_text(encoding="utf-8")
    start = text.find('id       = "%s"' % rec_id)
    if start == -1:
        start = text.find('id = "%s"' % rec_id)
    if start == -1:
        raise SystemExit("cannot find record %r in %s" % (rec_id, file_name))
    nxt = text.find("\n[[", start)
    end = len(text) if nxt == -1 else nxt
    body = text[start:end]

    block = (
        "\n# Solved by scripts/solve-split.py, never written by hand.\n"
        "# [words, pictures] in px. At these two widths the two columns end at\n"
        "# the same height. Widths, not a ratio: see .setup-split in style.css.\n"
        "split_en = [%d, %d]\n"
        "split_zh = [%d, %d]\n" % (en[0], en[1], zh[0], zh[1]))

    cleaned = re.sub(
        r"\n# Solved by scripts/solve-split\.py[^\n]*\n"
        r"(?:#[^\n]*\n)*"
        r"split_en = \[[^\]]*\]\n"
        r"split_zh = \[[^\]]*\]\n", "\n", body)
    cleaned = re.sub(r"\nsplit_(?:en|zh) = \[[^\]]*\]\n", "\n", cleaned)
    cleaned = cleaned.rstrip("\n")
    path.write_text(text[:start] + cleaned + "\n" + block + "\n" + text[end:],
                    encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write the solved widths into _data/ (default: report only)")
    ap.add_argument("--only", help="one record id")
    ap.add_argument("--lo", type=int, default=200)
    ap.add_argument("--hi", type=int, default=1120)
    ap.add_argument("--step", type=int, default=2)
    args = ap.parse_args()

    if not SITE.is_dir():
        sys.exit("no __site/. Build first:\n"
                 "  julia --project=. -e 'using Franklin; serve(single=true, launch=false)'")
    edge = EDGE if EDGE.is_file() else EDGE_ALT
    if not edge.is_file():
        sys.exit("no msedge.exe found")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(SITE))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    except OSError:
        sys.exit("port %d is already in use" % PORT)
    httpd.log_message = lambda *a, **k: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    todo = [r for r in records() if not args.only or r["id"] == args.only]
    if not todo:
        sys.exit("no page composes a split block"
                 + (" for %r" % args.only if args.only else ""))

    probe = PROBE % (args.lo, args.hi, args.step)
    browser = cdp.Browser(edge, ROOT / "_tmp" / "profile-solve")
    solved, failed = [], []
    try:
        browser.call("Page.enable")
        browser.call("Emulation.setDeviceMetricsOverride", {
            "width": VIEWPORT, "height": 3000, "deviceScaleFactor": 1,
            "mobile": False})
        for rec in todo:
            per_lang = {}
            for lang, route in rec["routes"].items():
                browser.clear_events()
                browser.call("Page.navigate",
                             {"url": "http://127.0.0.1:%d%s" % (PORT, route)})
                browser.await_event("Page.loadEventFired", timeout=45)
                # ET Book must be down before anything is measured. Falling
                # back to Times mid-sweep would poison every number.
                browser.evaluate("document.fonts.ready.then(function(){return 1})")
                time.sleep(0.35)
                per_lang[lang] = solve(browser.evaluate(probe))
            rec["solved"] = per_lang
            en, zh = per_lang["en"], per_lang["zh"]
            if en.get("error") or zh.get("error"):
                failed.append(rec)
                print("  FAIL %-44s %s" % (rec["id"],
                                           en.get("error") or zh.get("error")))
                continue
            solved.append(rec)
            note = "  THIN, pictures fill %.0f%% of their column" % (100 * en["fill"]) \
                if en["thin"] else ""
            same = "" if (en["words"], en["pics"]) == (zh["words"], zh["pics"]) \
                else "   zh differs: [%d, %d]" % (zh["words"], zh["pics"])
            print("  ok   %-44s words %4d  pics %4d  %4.1f chars  level to "
                  "%.2fpx%s%s" % (rec["id"], en["words"], en["pics"], en["cpl"],
                                  abs(en["err"]), same, note))
    finally:
        browser.close()
        httpd.shutdown()
        httpd.server_close()

    if args.write:
        for rec in solved:
            e, z = rec["solved"]["en"], rec["solved"]["zh"]
            write_split(rec["file"], rec["key"], rec["id"],
                        (e["words"], e["pics"]), (z["words"], z["pics"]))
        print("\nwrote %d record(s) to _data/. Rebuild, then run:\n"
              "  python scripts/shoot.py --emulate --sweep setup "
              "--widths 1440,390,320 --measure" % len(solved))
    else:
        print("\n%d solved, %d could not be. Nothing written; pass --write."
              % (len(solved), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
