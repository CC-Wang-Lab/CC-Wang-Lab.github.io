#!/usr/bin/env python3
"""
Screenshots the BUILT site in both themes, at several widths, with motion off.

Build first:
    julia --project=. -e 'using Franklin; optimize(minify=false, prerender=false)'
Then:
    python scripts/shoot.py                 # the standard 16-shot matrix
    python scripts/shoot.py --url / --width 1440 --theme dark
    python scripts/shoot.py --keep-server   # leave it running to poke by hand

Output goes to _tmp/verify/, which is in .gitignore and in the Franklin
`ignore` list in config.md.

Five things here are not decoration:

1. EDGE, NEVER CHROME. `chrome.exe --headless` attaches to the Chrome instance
   already running on this machine, exits 0 and writes no file.

2. The theme is forced by SEEDING localStorage from the query string, through a
   script injected right after <head> and therefore before theme-init.js. The
   simpler trick, setting data-bs-theme directly, would bypass theme-init.js
   entirely, so a broken theme-init.js would still screenshot a perfect page.
   Each launch gets a throwaway --user-data-dir, so the forced theme can never
   leak into the reviewer's own browser. That leak has already caused one false
   bug report, when a paused marquee was reported as broken.

3. --virtual-time-budget fast-forwards the page. Without `__motion=off` that
   runs past the news slider's 6 s dwell and you screenshot an arbitrary slide.

4. SCROLL-LINKED EFFECTS CANNOT BE MEASURED HERE. Under --virtual-time-budget
   this headless window never produces a frame, so requestAnimationFrame never
   fires. The site throttles its scroll handler with rAF, so the progress bar
   and the hero drift sit at their starting values and look broken when they
   are not. The audit PROBES rAF and says which it is, rather than reporting a
   false failure. Dropping the budget (--realtime) makes rAF work, but Edge
   then shoots at load and exits, so the audit never finishes; the two flags
   refuse to run together. The reveal effect is unaffected and fully covered,
   because IntersectionObserver does fire. Measured 2026-08-20.

5. msedge.exe RETURNS BEFORE IT HAS WRITTEN THE FILE. The binary you launch is
   a stub: it hands the work to a detached process and exits 0 immediately, so
   `subprocess.run` returning tells you nothing. The PNG lands about 3 s later.
   Measured 2026-08-19: waiting on the exit code gave 0 shots out of 16, and
   polling for the file gave 16 out of 16 from the same command line. This is
   also what "Edge exits 0 and writes nothing" really was; it is not an orphan
   process holding a profile.
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import time
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "__site"
OUT = ROOT / "_tmp" / "verify"
PORT = 8123
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

SEED = """<script>
/* Injected by scripts/shoot.py. Runs before theme-init.js so the real
   theme code path is exercised, not bypassed. */
(function () {
  var q = new URLSearchParams(location.search);
  try {
    if (q.get("__theme")) localStorage.setItem("labTheme", q.get("__theme"));
    if (q.get("__motion")) localStorage.setItem("labMotion", q.get("__motion"));
  } catch (e) {}
  /* __scrollto=0.35 shoots the page a third of the way down, which is the only
     way to see a scroll-linked effect in a still: the progress bar under the
     navbar and the hero drifting behind it. */
  var to = q.get("__scrollto");
  if (to) {
    window.addEventListener("load", function () {
      setTimeout(function () {
        var span = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo(0, Math.round(span * parseFloat(to)));
      }, 700);
    });
  }
})();
</script>"""

AUDIT = """<script>
/* Injected by scripts/shoot.py --measure. Reports the two things a grep over
   style.css cannot see, because both are COMPUTED: the final font-size of
   every element that really renders text, and anything wider than the
   viewport. */
window.addEventListener("load", function () {
  /* Scroll the whole page first. The reveal effect only shows a block when it
     comes into view, so measuring at the top would call every block below the
     fold "hidden" and be wrong. Sweep down, sweep back, then measure. */
  var STEPS = 14, step = 0, mid = { bar: null, hero: null, at: null };

  /* The page's scroll handler is rAF-throttled, so reading a scroll-linked
     value straight after scrollTo reads the PREVIOUS frame. Two frames later
     the handler has definitely written. Getting this wrong made the progress
     bar look dead when it was working. */
  /* rAF is probed rather than relied on. Under --virtual-time-budget a
     headless window may never produce a frame, and the site's scroll handler
     is rAF-throttled, so a dead rAF makes a working effect look broken. Report
     which it is instead of guessing. */
  var rafFired = false;
  requestAnimationFrame(function () { rafFired = true; });

  function sampleAfterAFrame(done) {
    setTimeout(function () {
      var span = document.documentElement.scrollHeight - window.innerHeight;
      var b = document.querySelector(".scroll-progress");
      var hi = document.querySelector(".hero-inner");
      mid.at = Math.round((window.pageYOffset / (span || 1)) * 100) / 100;
      if (b) mid.bar = getComputedStyle(b).transform;
      if (hi) mid.hero = hi.style.transform + " opacity:" + (hi.style.opacity || "");
      done();
    }, 350);
  }

  function sweep() {
    var span = document.documentElement.scrollHeight - window.innerHeight;
    if (step <= STEPS) {
      window.scrollTo(0, Math.round((span * step) / STEPS));
      var isMid = step === Math.round(STEPS / 2);
      step++;
      if (isMid) {
        sampleAfterAFrame(function () {
          setTimeout(sweep, 140);
        });
        return;
      }
      setTimeout(sweep, 140);
      return;
    }
    window.scrollTo(0, 0);
    setTimeout(measure, 2500);
  }
  setTimeout(sweep, 200);

  function measure() {
    function sel(e) {
      var c = (typeof e.className === "string" ? e.className : "").trim();
      return e.tagName.toLowerCase() + (c ? "." + c.split(/[ ]+/).slice(0, 2).join(".") : "");
    }
    function clipped(e) {
      for (var a = e.parentElement; a && a !== document.body; a = a.parentElement) {
        var o = getComputedStyle(a);
        if (o.overflowX === "hidden" || o.overflowX === "clip" ||
            o.overflow === "hidden" || o.overflow === "clip") return true;
      }
      return false;
    }
    var floor = 12.8, small = [], wide = [], seen = {};
    var docW = document.documentElement.clientWidth;
    var all = document.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) {
      var el = all[i], cs = getComputedStyle(el), r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      /* The contact form's honeypot lives at left:-9999px on purpose, and so
         does every other visually-hidden control. Parked off-screen is not
         overflowing. */
      if (r.right < -100) continue;
      if (cs.visibility === "hidden" || cs.opacity === "0") continue;
      /* A partners-marquee track is 5055px wide inside a 1440px viewport with
         overflow:hidden, and the slider progress bar is translated off to the
         left. Both are deliberate clipped tracks, so anything with a clipping
         ancestor is not an overflow. The page-level check below is what
         actually matters: scrollWidth against clientWidth. */
      if (clipped(el)) continue;
      if (r.right > docW + 1 || r.left < -1) {
        wide.push(sel(el) + " left=" + Math.round(r.left) + " right=" + Math.round(r.right));
      }
      var own = "";
      for (var n = 0; n < el.childNodes.length; n++) {
        if (el.childNodes[n].nodeType === 3) own += el.childNodes[n].nodeValue;
      }
      if (!own.trim()) continue;
      var fs = parseFloat(cs.fontSize);
      /* Exactly 0 is never an accident: it is the icon-only idiom that
         collapses a button label below 576px, and .motion-toggle .bi resets
         it. Anything between 0 and the floor is a real defect. */
      if (fs > 0 && fs < floor - 0.01) {
        var k = sel(el) + "@" + fs;
        if (!seen[k]) { seen[k] = 1; small.push(sel(el) + " = " + fs.toFixed(2) + "px"); }
      }
    }
    /* The failure this whole check exists for: a block the reveal hid and
       never un-hid. After a full sweep, every one of them must be .is-in. */
    var claimed = document.querySelectorAll("[data-reveal]");
    var stuck = [];
    for (var q = 0; q < claimed.length; q++) {
      var c = claimed[q];
      if (!c.classList.contains("is-in")) {
        stuck.push(sel(c) + " top=" + Math.round(c.getBoundingClientRect().top));
      }
    }
    fetch("/__report", { method: "POST", body: JSON.stringify({
      url: location.pathname, w: window.innerWidth,
      motion: document.documentElement.classList.contains("motion-off") ? "off" : "on",
      revealTotal: claimed.length, revealStuck: stuck.slice(0, 10),
      progressBar: !!document.querySelector(".scroll-progress"),
      midAt: mid.at, midBar: mid.bar, midHero: mid.hero, rafFired: rafFired,
      theme: document.documentElement.getAttribute("data-bs-theme"),
      scrollWidth: document.documentElement.scrollWidth, clientWidth: docW,
      etbook: document.fonts.check("1em et-book"),
      loaded: document.body.classList.contains("loaded"),
      belowFloor: small, overflowing: wide.slice(0, 14)
    })});
  }
});
</script>"""

REPORTS = []
MOTION = ["off"]    # set from --motion; a list so shoot() can read it
SCROLLTO = [""]     # set from --scrollto
REALTIME = [False]  # set from --realtime

# page, width, theme, why this shot exists
MATRIX = [
    ("/", 492, "light", "bottom of the fluid ramp: hero at the clamp minimum, stacked buttons"),
    ("/", 768, "light", "the 991.98 block with the 767.98 block off, cards 2-up"),
    ("/", 1440, "light", "the reference shot"),
    ("/", 1920, "light", "top of the ramp: hero at the clamp maximum, measure holding at 74ch"),
    ("/", 492, "dark", "dark tokens at the narrow end"),
    ("/", 1440, "dark", "dark parity: diff against the 1440 light shot, only colour should move"),
    ("/publications/", 492, "light", "smallest type at the narrowest width Edge allows"),
    ("/publications/", 1440, "light", "densest small type, the longest run of --fs-xs"),
    ("/people/", 1440, "light", "five card sections plus the person table"),
    ("/people/", 1440, "dark", "the same in dark"),
    ("/contact/", 600, "light", "closes the 576-767.98 hole nothing else lands in"),
    ("/contact/", 1440, "light", "form labels, input borders, the required chip"),
    ("/contact/", 1440, "dark", "input borders in dark, where the 3:1 rule is judged by eye"),
    ("/zh/", 1440, "light", "CJK at the new sizes, the reason the font stack matters"),
    ("/zh/", 1440, "dark", "the fourth corner of theme times language"),
    ("/zh/people/cc-wang/", 1440, "dark", "biggest type, CJK and dark at once"),
]


def insert_head(html, snippet):
    """Put `snippet` as early in the document as it can possibly go.

    NOT a regex for `<head[^>]*>`. Franklin's minifier DELETES the optional
    <head> tag, and `<head[^>]*>` then happily matches `<header>` further down
    the body, which put the theme seed AFTER theme-init.js had already read
    localStorage. Every "dark" shot came out light and the harness said nothing.
    Measured 2026-08-20.
    """
    for pattern in (r"<head(?=[\s>])[^>]*>", r"<html(?=[\s>])[^>]*>", r"<!DOCTYPE[^>]*>"):
        m = re.search(pattern, html, re.I)
        if m:
            return html[:m.end()] + snippet + html[m.end():], 1
    return html, 0


class Injector(http.server.SimpleHTTPRequestHandler):
    """Serves __site/ read-only, injecting the seed script into every page."""

    def translate_path(self, path):
        # Hand the query and fragment off first, then let the base class do the
        # percent-decoding and the `..` sanitising. Re-implementing either is
        # how a read-only dev server turns into a file-disclosure hole.
        clean = path.split("?", 1)[0].split("#", 1)[0]
        # `directory=` is set at construction, so the base class resolves
        # against __site/ and not against the process working directory.
        p = Path(super().translate_path(clean))
        if p.is_dir():
            p = p / "index.html"
        return str(p)

    measure = False

    def do_POST(self):
        if self.path == "/__report":
            n = int(self.headers.get("Content-Length", 0))
            REPORTS.append(json.loads(self.rfile.read(n).decode("utf-8")))
            self.send_response(204)
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        p = Path(self.translate_path(self.path))
        if p.suffix.lower() in (".html", ".htm") and p.is_file():
            html = p.read_text(encoding="utf-8")
            html, n = insert_head(html, SEED + (AUDIT if Injector.measure else ""))
            if n != 1:
                self.send_error(500, "no <head> in " + str(p))
                return
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *a):
        pass


def find_edge():
    for c in (EDGE, EDGE_ALT):
        if c.is_file():
            return c
    sys.exit("Edge not found. Chrome headless does not work on this machine; see the docstring.")


# `html { scrollbar-gutter: stable }` reserves the scrollbar even when
# --hide-scrollbars is on, so the layout viewport is always this much narrower
# than --window-size. Measured on Edge 151: exactly 24px at every width.
GUTTER = 24
# Headless Edge on Windows will not open a window narrower than about 508 DIP.
# Ask for 375 and it lays the page out at 484 CSS px and then CROPS the
# screenshot to 375, which reads as the site overflowing when it does not.
# Doubling --force-device-scale-factor does not help: the clamp is on DIP, not
# on physical pixels. So 484 is the narrowest honest width here. It still sits
# inside both the 575.98 and the 767.98 media blocks, so nothing is untested
# except the very narrow phone layout, which has to be checked by hand in
# devtools. Measured 2026-08-19.
NARROWEST = 492


def shoot(edge, url, width, theme, out_png, profile, height=4000, budget=9000):
    dsf = 1
    win = max(width, NARROWEST) + GUTTER
    cmd = [
        str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=%d" % dsf, "--force-color-profile=srgb",
        "--disable-lcd-text", "--no-first-run", "--no-default-browser-check",
        "--disable-extensions", "--disable-sync",
        "--disable-features=Translate,MediaRouter,OptimizationHints",
        # NEVER add --remote-debugging-port: that is the flag that makes a
        # Chromium binary attach to an instance already running.
        "--user-data-dir=" + str(profile),
        "--window-size=%d,%d" % (win, height),
        # --realtime drops the budget: virtual time never produces frames, so
        # rAF never fires and a scroll-linked effect cannot be measured.
    ] + ([] if REALTIME[0] else ["--virtual-time-budget=%d" % budget]) + [
        "--screenshot=" + str(out_png),
        "http://127.0.0.1:%d%s?__theme=%s&__motion=%s%s"
        % (PORT, url, theme, MOTION[0], SCROLLTO[0]),
    ]
    if out_png.exists():
        out_png.unlink()
    subprocess.run(cmd, capture_output=True, timeout=120)
    # See point 4 in the module docstring: the exit code is not the signal.
    # Poll for the file, then for its size to stop growing.
    deadline = time.monotonic() + 60
    last = -1
    while time.monotonic() < deadline:
        if out_png.is_file():
            size = out_png.stat().st_size
            if size > 0 and size == last:
                return True
            last = size
        time.sleep(0.4)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--theme", default="light", choices=["light", "dark"])
    ap.add_argument("--height", type=int, default=4000)
    ap.add_argument("--keep-server", action="store_true")
    ap.add_argument("--realtime", action="store_true",
                    help="drop --virtual-time-budget. Slower, but it is the "
                         "only way rAF fires, so scroll-linked effects can be "
                         "measured at all.")
    ap.add_argument("--scrollto", type=float, default=None,
                    help="shoot the page at this fraction of its scroll range, "
                         "0..1, so scroll-linked effects are visible in a still")
    ap.add_argument("--motion", default="off", choices=["on", "off"],
                    help="seed localStorage.labMotion. Default off, which "
                         "freezes the marquee and the slider so shots are "
                         "diffable. Use on to test the scroll effects.")
    ap.add_argument("--measure", action="store_true",
                    help="report computed font sizes below the 12.8px "
                         "floor and anything wider than the viewport")
    args = ap.parse_args()

    if args.measure and args.realtime:
        sys.exit("--measure and --realtime cannot be combined. Without the "
                 "virtual-time budget Edge screenshots at load and exits, so "
                 "the audit's scroll sweep never finishes and nothing is "
                 "reported. Measured 2026-08-20.")
    if not (SITE / "index.html").is_file():
        sys.exit("__site/ is not built. Run Franklin.optimize() first.")
    Injector.measure = args.measure
    MOTION[0] = args.motion
    REALTIME[0] = args.realtime
    SCROLLTO[0] = ("&__scrollto=%g" % args.scrollto) if args.scrollto else ""
    edge = find_edge()
    OUT.mkdir(parents=True, exist_ok=True)

    # NOT allow_reuse_address. On Windows SO_REUSEADDR lets a SECOND server bind
    # a port a first one is already listening on, and requests then go to
    # whichever won the race. A run killed by `timeout` leaves its server alive,
    # and the next run silently gets answered by the OLD code. That cost an hour:
    # the theme seed looked broken when the real fault was three stale servers.
    # Leaving it at the default makes a stale server a loud error instead.
    socketserver.TCPServer.allow_reuse_address = False
    handler = functools.partial(Injector, directory=str(SITE))
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    except OSError:
        # Killing this script from outside (a `timeout`, a Ctrl-C during a
        # launch) skips the teardown and leaves the socket held.
        sys.exit("port %d is already in use. A previous run was killed before "
                 "it could clean up. Find it with `netstat -ano | findstr "
                 ":%d` and `taskkill /PID <pid> /F`." % (PORT, PORT))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print("serving %s on 127.0.0.1:%d (read-only, injecting)" % (SITE, PORT))

    shots = ([(args.url, args.width, args.theme, "ad hoc")] if args.url else MATRIX)
    made, failed = [], []
    try:
        for i, (url, width, theme, why) in enumerate(shots):
            slug = (url.strip("/").replace("/", "-") or "home")
            # NARROWEST, not `width`: below it Edge renders wider than asked,
            # and a file called _375_ that is really 492 is a lie.
            real = max(width, NARROWEST)
            png = OUT / ("%02d_%s_%d_%s.png" % (i, slug, real, theme))
            profile = OUT / ("profile-%02d" % i)
            ok = shoot(edge, url, width, theme, png, profile, args.height)
            kb = png.stat().st_size // 1024 if ok else 0
            print("  %s %-28s %5d %-5s %6d KB  %s"
                  % ("ok  " if ok else "FAIL", url, width, theme, kb, why))
            (made if ok else failed).append(str(png))
    finally:
        if args.keep_server:
            print("\nserver still running on %d. Ctrl-C to stop." % PORT)
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                pass
        httpd.shutdown()
        httpd.server_close()
        for d in OUT.glob("profile-*"):
            shutil.rmtree(d, ignore_errors=True)

    if args.measure:
        print("\n=== COMPUTED AUDIT ===")
        if len(REPORTS) < len(made):
            print("  %d shot(s) but only %d report(s): the audit did not run on "
                  "every page, so this is NOT a clean result."
                  % (len(made), len(REPORTS)))
            return 1
        bad = 0
        for r in REPORTS:
            over = r["scrollWidth"] - r["clientWidth"]
            flags = []
            if r["belowFloor"]:
                flags.append("%d below the 12.8px floor" % len(r["belowFloor"]))
            if over > 1:
                flags.append("page %dpx wider than the viewport" % over)
            if not r["etbook"]:
                flags.append("ET BOOK DID NOT LOAD")
            if not r["loaded"]:
                flags.append("body.loaded never set")
            if r.get("revealStuck"):
                flags.append("%d BLOCK(S) LEFT HIDDEN BY THE REVEAL: %s"
                             % (len(r["revealStuck"]), ", ".join(r["revealStuck"])))
            if r.get("motion") == "on" and not r.get("progressBar"):
                flags.append("no scroll-progress bar")
            # The scroll-linked values are REPORTED, never asserted. rAF fires
            # only sometimes in this headless window, so a zero here means "not
            # sampled" at least as often as it means "broken", and asserting on
            # it produces false failures. The printed line below is the
            # evidence; read it. Confirmed working 2026-08-20: bar scaleX
            # 0.3573 at half the page and 1.0 at the end, hero drifted 113.6px
            # and faded to 0.
            bad += len(flags)
            print("  %-22s %5dpx %-5s motion=%-3s reveal=%-3s  %s"
                  % (r["url"], r["w"], r["theme"], r.get("motion", "?"),
                     r.get("revealTotal", "?"), "; ".join(flags) or "clean"))
            for x in r["belowFloor"]:
                print("        floor  " + x)
            for x in r["overflowing"]:
                print("        wide   " + x)
            if r.get("midBar") or r.get("midHero"):
                print("        scroll at %s of the page: bar %s | hero %s"
                      % (r.get("midAt"), r.get("midBar"), r.get("midHero")))
        stalled = [r["url"] for r in REPORTS
                   if r.get("motion") == "on" and not r.get("rafFired")]
        if stalled:
            print("")
            print("  NOTE  requestAnimationFrame never fired on %d page(s),"
                  " so the progress bar and the hero drift" % len(stalled))
            print("        could not be measured there. Harness limit, see"
                  " point 4 in the docstring.")
            print("        The reveal effect IS covered above.")
        print("\n" + ("AUDIT CLEAN" if not bad else "%d finding(s)" % bad))

    print("\n%d shot(s) in %s" % (len(made), OUT))
    if failed:
        print("%d FAILED. A blank or missing PNG is usually `body { opacity: 0 }` "
              "waiting for a window `load` that never fired because a CDN asset "
              "stalled." % len(failed))
        return 1
    print("Profiles deleted. Nothing was written to __site/.")
    print("Reminder: clear localStorage labMotion and labTheme in your OWN browser "
          "if you have been testing there by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
