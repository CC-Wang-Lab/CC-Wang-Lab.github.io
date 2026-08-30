#!/usr/bin/env python3
"""
Screenshots the BUILT site in both themes, at several widths, with motion off.

Build first:
    julia --project=. -e 'using Franklin; optimize(minify=false, prerender=false)'
Then:
    python scripts/shoot.py                 # the full regression matrix
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
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
    var floor = 12.8, targetFloor = 44;
    var small = [], wide = [], undersizedTargets = [], unboundedReading = [], seen = {};
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
    /* Controls that behave like buttons use one shared 44px comfort target.
       Ordinary inline links are deliberately absent: WCAG's target-spacing
       exception applies to text flowing inside a sentence. */
    var targetSelector = [
      ".btn-cta", ".btn-ghost", ".btn-icon", ".navbar-toggler",
      ".lab-nav .nav-link", ".motion-toggle", ".ns-arrow",
      ".ns-nav-item", ".pt-viewport", ".pg-chip", ".pi-chip",
      ".profile-layout-choice", ".profile-design-link",
      ".foot-nav a", "#backToTop", ".ff input", ".ff textarea", ".ff select"
    ].join(",");
    var targets = document.querySelectorAll(targetSelector);
    var targetSeen = {};
    function shownRect(target) {
      /* The mobile navbar, hidden carousel arrows and back-to-top control are
         still real controls. Reveal only display:none ancestors for the few
         microseconds needed to measure, then restore every inline style. */
      var changed = [];
      for (var node = target; node && node !== document.documentElement; node = node.parentElement) {
        if (getComputedStyle(node).display === "none") {
          changed.push([node, node.getAttribute("style")]);
          node.style.setProperty("display", node === target ? "inline-flex" : "block", "important");
        }
      }
      var rect = target.getBoundingClientRect();
      for (var c = changed.length - 1; c >= 0; c--) {
        if (changed[c][1] === null) changed[c][0].removeAttribute("style");
        else changed[c][0].setAttribute("style", changed[c][1]);
      }
      return rect;
    }
    for (var t = 0; t < targets.length; t++) {
      var target = targets[t], targetRect = shownRect(target);
      if (targetRect.width < targetFloor - 0.5 || targetRect.height < targetFloor - 0.5) {
        var targetKey = sel(target) + "@" + Math.round(targetRect.width) + "x" + Math.round(targetRect.height);
        if (!targetSeen[targetKey]) {
          targetSeen[targetKey] = 1;
          undersizedTargets.push(sel(target) + " = " +
            targetRect.width.toFixed(1) + "x" + targetRect.height.toFixed(1) + "px");
        }
      }
    }
    /* These blocks carry long-form reading text. Their media and parent grids
       stay full-width, but the text block itself must declare a readable cap. */
    var readingSelector = [
      ".pi-body", ".profile-narrative", ".pub-theme", ".project-body > h2",
      ".project-body > h3", ".project-body > h4",
      ".project-body > p:not(:has(img, picture, video))",
      ".project-body > ul", ".project-body > ol",
      ".project-body > blockquote"
    ].join(",");
    var reading = document.querySelectorAll(readingSelector);
    var readingSeen = {};
    function readingLimit(readingStyle) {
      var probe = document.createElement("span");
      probe.style.cssText = "position:fixed;visibility:hidden;display:block;" +
                            "width:var(--measure);pointer-events:none";
      probe.style.fontFamily = readingStyle.fontFamily;
      probe.style.fontSize = readingStyle.fontSize;
      probe.style.fontStyle = readingStyle.fontStyle;
      probe.style.fontWeight = readingStyle.fontWeight;
      document.body.appendChild(probe);
      var width = probe.getBoundingClientRect().width;
      probe.remove();
      return width;
    }
    for (var u = 0; u < reading.length; u++) {
      var readingStyle = getComputedStyle(reading[u]);
      if (readingStyle.display === "none" || readingStyle.visibility === "hidden") continue;
      var maxWidth = parseFloat(readingStyle.maxWidth);
      var limit = readingLimit(readingStyle);
      if (!isFinite(maxWidth) || maxWidth > limit + 1) {
        var readingKey = sel(reading[u]);
        if (!readingSeen[readingKey]) {
          readingSeen[readingKey] = 1;
          unboundedReading.push(readingKey + " max " + readingStyle.maxWidth +
            " exceeds " + limit.toFixed(1) + "px measure");
        }
      }
    }
    var narrowProjectMedia = [];
    var projectMedia = document.querySelectorAll([
      ".project-body > .project-figure",
      ".project-body > p:has(img, picture, video)"
    ].join(","));
    for (var m = 0; m < projectMedia.length; m++) {
      var mediaBlock = projectMedia[m];
      var mediaBody = mediaBlock.closest(".project-body");
      var mediaRect = mediaBlock.getBoundingClientRect();
      var bodyRect = mediaBody.getBoundingClientRect();
      var mediaNode = mediaBlock.querySelector("img,picture,video");
      var mediaNodeRect = mediaNode ? mediaNode.getBoundingClientRect() : mediaRect;
      if (mediaRect.width < bodyRect.width - 1 || mediaNodeRect.width < mediaRect.width - 1) {
        narrowProjectMedia.push(sel(mediaBlock) + " block/media/body = " +
          mediaRect.width.toFixed(1) + "/" + mediaNodeRect.width.toFixed(1) +
          "/" + bodyRect.width.toFixed(1) + "px");
      }
    }
    function tokenSize(token) {
      var probe = document.createElement("span");
      probe.style.cssText = "position:fixed;visibility:hidden;font-size:var(" + token + ")";
      document.body.appendChild(probe);
      var size = parseFloat(getComputedStyle(probe).fontSize);
      probe.remove();
      return size;
    }
    var smToken = tokenSize("--fs-sm"), xsToken = tokenSize("--fs-xs");
    var undersizedFunctional = [];
    var functional = document.querySelectorAll([
      ".hero-caption", ".project-figure figcaption", ".stat-label",
      ".person-table .person-row-head", ".pf-label", ".foot-head",
      ".ff-req", ".ns-head", ".pt-head", ".pt-note", ".pg-chip", ".pi-chip"
    ].join(","));
    for (var f = 0; f < functional.length; f++) {
      var functionalStyle = getComputedStyle(functional[f]);
      if (functionalStyle.display === "none" || functionalStyle.visibility === "hidden") continue;
      var functionalSize = parseFloat(functionalStyle.fontSize);
      var functionalFloor = functional[f].matches(".pg-chip,.pi-chip") ? smToken : xsToken;
      if (functionalSize < functionalFloor - 0.01) {
        undersizedFunctional.push(sel(functional[f]) + " = " +
          functionalSize.toFixed(2) + "px, expected at least " +
          functionalFloor.toFixed(2) + "px");
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
    var profileAudit = null;
    var profileShell = document.querySelector(".profile-layout");
    if (profileShell) {
      var profileAllowed = ["editorial", "dossier", "narrative"];
      var profileRequested = new URLSearchParams(location.search).get("profile-layout");
      var profileValid = profileAllowed.indexOf(profileRequested) !== -1;
      var profileExpected = profileValid ? profileRequested : "editorial";
      var profileRoot = document.documentElement;
      var profileName = document.querySelector(".person-hd .pi-heading");
      var profileIdentity = profileShell.querySelector(".profile-identity");
      var profileNarrative = profileShell.querySelector(".profile-narrative");
      var profileRecord = profileShell.querySelector(".profile-record");
      var profileRole = profileShell.querySelector(".profile-role");
      var profileSectionHead = profileShell.querySelector(".profile-narrative h2");
      var profileFactLabel = profileShell.querySelector(".pf-label");
      var profileFactValue = profileShell.querySelector(".pf-values");
      var profileSwitcher = document.querySelector("[data-profile-switcher]");
      var profileChoices = profileSwitcher ?
        profileSwitcher.querySelectorAll("[data-profile-layout-choice]") : [];
      var profileLanguageHref = document.querySelector(".lang-switch") ?
        document.querySelector(".lang-switch").getAttribute("href") : "";
      var profileCompareFlag = profileRoot.getAttribute("data-profile-layout-compare");
      var profileRects = [profileIdentity, profileNarrative, profileRecord]
        .filter(Boolean).map(function (node) { return node.getBoundingClientRect(); });
      function rectanglesOverlap(a, b) {
        return Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
               Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;
      }
      var profileOverlap = false;
      if (window.innerWidth > 991.98) {
        for (var pa = 0; pa < profileRects.length; pa++) {
          for (var pb = pa + 1; pb < profileRects.length; pb++) {
            if (rectanglesOverlap(profileRects[pa], profileRects[pb])) profileOverlap = true;
          }
        }
      }
      var profileMobileOrder = true;
      if (window.innerWidth <= 991.98 && profileName && profileIdentity &&
          profileNarrative && profileRecord) {
        var nameRect = profileName.getBoundingClientRect();
        var identityRect = profileIdentity.getBoundingClientRect();
        var narrativeRect = profileNarrative.getBoundingClientRect();
        var recordRect = profileRecord.getBoundingClientRect();
        profileMobileOrder = nameRect.bottom <= identityRect.top + 1 &&
          identityRect.bottom <= narrativeRect.top + 1 &&
          narrativeRect.bottom <= recordRect.top + 1;
      }
      var expectedNameToken = profileExpected === "dossier" ? "--fs-2xl" :
        (profileExpected === "narrative" ? "--fs-4xl" : "--fs-3xl");
      var interaction = { tested: false, passed: true };
      if (profileChoices.length === 3) {
        var alternative = Array.prototype.find.call(profileChoices, function (choice) {
          return choice.getAttribute("data-profile-layout-choice") !== profileExpected;
        });
        var original = Array.prototype.find.call(profileChoices, function (choice) {
          return choice.getAttribute("data-profile-layout-choice") === profileExpected;
        });
        if (alternative && original) {
          interaction.tested = true;
          var alternativeValue = alternative.getAttribute("data-profile-layout-choice");
          alternative.click();
          interaction.passed = profileRoot.getAttribute("data-profile-layout") === alternativeValue &&
            new URLSearchParams(location.search).get("profile-layout") === alternativeValue;
          original.click();
          interaction.passed = interaction.passed &&
            profileRoot.getAttribute("data-profile-layout") === profileExpected &&
            new URLSearchParams(location.search).get("profile-layout") === profileExpected;
        }
      }
      profileAudit = {
        requested: profileRequested || "",
        expected: profileExpected,
        applied: profileRoot.getAttribute("data-profile-layout"),
        compareFlag: profileCompareFlag,
        switcherVisible: !!profileSwitcher && !profileSwitcher.hidden,
        choiceCount: profileChoices.length,
        activeChoiceCount: profileSwitcher ?
          profileSwitcher.querySelectorAll('[aria-pressed="true"]').length : 0,
        regionCounts: {
          identity: profileShell.querySelectorAll(".profile-identity").length,
          narrative: profileShell.querySelectorAll(".profile-narrative").length,
          record: profileShell.querySelectorAll(".profile-record").length
        },
        nameFont: profileName ? parseFloat(getComputedStyle(profileName).fontSize) : 0,
        expectedNameFont: tokenSize(expectedNameToken),
        roleFont: profileRole ? parseFloat(getComputedStyle(profileRole).fontSize) : 0,
        expectedRoleFont: tokenSize("--fs-lg"),
        narrativeFont: profileNarrative ?
          parseFloat(getComputedStyle(profileNarrative).fontSize) : 0,
        expectedNarrativeFont: tokenSize("--fs-md"),
        sectionHeadFont: profileSectionHead ?
          parseFloat(getComputedStyle(profileSectionHead).fontSize) : 0,
        expectedSectionHeadFont: tokenSize("--fs-xl"),
        factLabelFont: profileFactLabel ?
          parseFloat(getComputedStyle(profileFactLabel).fontSize) : 0,
        expectedFactLabelFont: tokenSize("--fs-xs"),
        factValueFont: profileFactValue ?
          parseFloat(getComputedStyle(profileFactValue).fontSize) : 0,
        expectedFactValueFont: tokenSize("--fs-sm"),
        languageHref: profileLanguageHref,
        mobileOrder: profileMobileOrder,
        overlaps: profileOverlap,
        interaction: interaction
      };
    }
    var partnerAudit = null;
    var partnerRoot = document.getElementById("partners");
    if (partnerRoot) {
      var partnerViewports = partnerRoot.querySelectorAll(".pt-viewport");
      var partnerBands = partnerRoot.querySelectorAll(".pt-band");
      var partnerRows = partnerRoot.querySelectorAll(".pt-row");
      var partnerLogos = partnerRoot.querySelectorAll(".pt-logo");
      var partnerLabels = [];
      var namedControls = true, describedControls = true;
      var shortcutControls = true, tabbableControls = true, groupedControls = true;
      for (var pv = 0; pv < partnerViewports.length; pv++) {
        var partnerViewport = partnerViewports[pv];
        var partnerLabel = partnerViewport.getAttribute("aria-label") || "";
        var partnerDescription = partnerViewport.getAttribute("aria-describedby") || "";
        partnerLabels.push(partnerLabel);
        namedControls = namedControls && !!partnerLabel;
        describedControls = describedControls && !!partnerDescription &&
          !!document.getElementById(partnerDescription);
        shortcutControls = shortcutControls &&
          partnerViewport.getAttribute("aria-keyshortcuts") === "ArrowLeft ArrowRight";
        tabbableControls = tabbableControls && partnerViewport.tabIndex === 0;
        groupedControls = groupedControls && partnerViewport.getAttribute("role") === "group";
      }
      var duplicateRowsHidden = partnerRows.length === partnerBands.length * 2;
      var rowWidthsMatch = true;
      for (var pb = 0; pb < partnerBands.length; pb++) {
        var bandRows = partnerBands[pb].querySelectorAll(".pt-row");
        duplicateRowsHidden = duplicateRowsHidden && bandRows.length === 2 &&
          !bandRows[0].hasAttribute("aria-hidden") &&
          bandRows[1].getAttribute("aria-hidden") === "true";
        if (bandRows.length === 2) {
          rowWidthsMatch = rowWidthsMatch &&
            Math.abs(bandRows[0].getBoundingClientRect().width -
                     bandRows[1].getBoundingClientRect().width) <= 1;
        }
      }
      var logosUnframed = true, logosLoaded = true, filtersPresent = true;
      for (var pl = 0; pl < partnerLogos.length; pl++) {
        var logo = partnerLogos[pl];
        var logoFrame = logo.closest(".pt-logo-frame");
        logosUnframed = logosUnframed && !logoFrame;
        logosLoaded = logosLoaded && logo.complete && logo.naturalWidth > 0;
        filtersPresent = filtersPresent && getComputedStyle(logo).filter !== "none";
      }
      var partnerKeyboard = { tested: false, passed: false, motionPaused: false };
      if (window.__partners && window.__partners.bands &&
          window.__partners.bands.length === 2 && partnerViewports.length === 2) {
        partnerKeyboard.tested = true;
        partnerKeyboard.motionPaused = !!window.LabMotion &&
          typeof window.LabMotion.isRunning === "function" &&
          !window.LabMotion.isRunning();
        var firstBand = window.__partners.bands[0];
        var secondBand = window.__partners.bands[1];
        var firstState = {
          nudge: firstBand.nudge, pos: firstBand.pos, base: firstBand.base,
          baseTime: firstBand.baseTime, transform: firstBand.track.style.transform
        };
        var secondState = {
          nudge: secondBand.nudge, pos: secondBand.pos, base: secondBand.base,
          baseTime: secondBand.baseTime, transform: secondBand.track.style.transform
        };
        partnerViewports[0].focus({ preventScroll: true });
        var rightKey = new KeyboardEvent("keydown", {
          key: "ArrowRight", bubbles: true, cancelable: true
        });
        document.activeElement.dispatchEvent(rightKey);
        var firstAfterRight = firstBand.nudge;
        var firstTransformAfterRight = firstBand.track.style.transform;
        var secondAfterRight = secondBand.nudge;
        var secondTransformAfterRight = secondBand.track.style.transform;
        var firstFocused = document.activeElement === partnerViewports[0];
        partnerViewports[1].focus({ preventScroll: true });
        var leftKey = new KeyboardEvent("keydown", {
          key: "ArrowLeft", bubbles: true, cancelable: true
        });
        document.activeElement.dispatchEvent(leftKey);
        partnerKeyboard.passed = rightKey.defaultPrevented && leftKey.defaultPrevented &&
          firstFocused && document.activeElement === partnerViewports[1] &&
          firstAfterRight > firstState.nudge && secondAfterRight === secondState.nudge &&
          firstTransformAfterRight !== firstState.transform &&
          secondTransformAfterRight === secondState.transform &&
          firstBand.nudge === firstAfterRight && secondBand.nudge < secondState.nudge &&
          firstBand.track.style.transform === firstTransformAfterRight &&
          secondBand.track.style.transform !== secondState.transform;
        [firstBand, secondBand].forEach(function (band, index) {
          var state = index === 0 ? firstState : secondState;
          band.nudge = state.nudge;
          band.pos = state.pos;
          band.base = state.base;
          band.baseTime = state.baseTime;
          band.track.style.transform = state.transform;
        });
        partnerViewports[1].blur();
      }
      partnerAudit = {
        arrowCount: partnerRoot.querySelectorAll(".pt-arrow,.pt-prev,.pt-next").length,
        viewportCount: partnerViewports.length,
        namedControls: namedControls,
        uniqueLabels: new Set(partnerLabels).size === partnerViewports.length,
        describedControls: describedControls,
        shortcutControls: shortcutControls,
        tabbableControls: tabbableControls,
        groupedControls: groupedControls,
        bandCount: partnerBands.length,
        rowCount: partnerRows.length,
        duplicateRowsHidden: duplicateRowsHidden,
        rowWidthsMatch: rowWidthsMatch,
        logoCount: partnerLogos.length,
        logosUnframed: logosUnframed,
        logosLoaded: logosLoaded,
        filtersPresent: filtersPresent,
        keyboard: partnerKeyboard
      };
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
      bodyFont: parseFloat(getComputedStyle(document.body).fontSize),
      smFont: smToken, xsFont: xsToken,
      belowFloor: small, undersizedTargets: undersizedTargets.slice(0, 24),
      undersizedFunctional: undersizedFunctional.slice(0, 16),
      unboundedReading: unboundedReading.slice(0, 12),
      narrowProjectMedia: narrowProjectMedia.slice(0, 8),
      overflowing: wide.slice(0, 14), profile: profileAudit, partners: partnerAudit
    })});
  }
});
</script>"""

REPORTS = []
MOTION = ["off"]    # set from --motion; a list so shoot() can read it
SCROLLTO = [None]   # set from --scrollto
REALTIME = [False]  # set from --realtime

# page, width, theme, why this shot exists
MATRIX = [
    ("/", 492, "light", "bottom of the fluid ramp: hero at the clamp minimum, stacked buttons"),
    ("/", 768, "light", "the 991.98 block with the 767.98 block off, cards 2-up"),
    ("/", 1440, "light", "the reference shot"),
    ("/", 1920, "light", "top of the ramp: hero at the clamp maximum, measure holding at 74ch"),
    ("/", 492, "dark", "dark tokens at the narrow end"),
    ("/", 1440, "dark", "dark parity: diff against the 1440 light shot, only colour should move"),
    ("/projects/", 492, "light", "filter chips and project cards at the narrow end"),
    ("/projects/", 1440, "light", "project list and filters at the reference width"),
    ("/projects/", 1440, "dark", "project list theme parity"),
    ("/projects/cpu-cooler-airflow/", 492, "light", "project prose and full-width media on mobile"),
    ("/projects/cpu-cooler-airflow/", 1440, "light", "project prose measure beside full-width media"),
    ("/projects/cpu-cooler-airflow/", 1440, "dark", "project detail theme parity"),
    ("/people/", 492, "light", "stacked people index and narrow footer"),
    ("/publications/", 492, "light", "smallest type at the narrowest width Edge allows"),
    ("/publications/", 1440, "light", "densest small type, the longest run of --fs-xs"),
    ("/publications/", 1440, "dark", "publication measure and theme parity"),
    ("/people/", 1440, "light", "five card sections plus the person table"),
    ("/people/", 1440, "dark", "the same in dark"),
    ("/contact/", 492, "light", "map sizing and stacked footer below 576px"),
    ("/contact/", 600, "light", "closes the 576-767.98 hole nothing else lands in"),
    ("/contact/", 1440, "light", "form labels, input borders, the required chip"),
    ("/contact/", 1440, "dark", "input borders in dark, where the 3:1 rule is judged by eye"),
    ("/zh/", 492, "light", "CJK headline, controls and footer at the narrow end"),
    ("/zh/", 1440, "light", "CJK at the new sizes, the reason the font stack matters"),
    ("/zh/", 1440, "dark", "the fourth corner of theme times language"),
    ("/zh/people/cc-wang/", 1440, "light", "Chinese professor page in light"),
    ("/zh/people/cc-wang/", 1440, "dark", "biggest type, CJK and dark at once"),
]

# Every real profile, language, layout and theme shares one content DOM. The
# full cross-product is intentional: a selector that accidentally scopes to an
# English route or one theme can otherwise look correct in every spot-check.
for language, prefix in (("English", "/"), ("Chinese", "/zh/")):
    for person in ("cc-wang", "maysam-gholampour"):
        for layout in ("editorial", "dossier", "narrative"):
            for theme in ("light", "dark"):
                MATRIX.append((
                    f"{prefix}people/{person}/?profile-layout={layout}",
                    1440,
                    theme,
                    f"{language} {person} {layout} profile variant",
                ))

for layout in ("editorial", "dossier", "narrative"):
    MATRIX.append((
        f"/people/cc-wang/?profile-layout={layout}",
        492,
        "light",
        f"shared mobile order for the {layout} profile variant",
    ))

MATRIX.extend([
    ("/people/cc-wang/", 492, "light", "normal profile visit shows all three layout controls"),
    ("/people/cc-wang/?profile-layout=invalid", 492, "light", "invalid profile query falls back safely"),
    ("/profile-designs/", 492, "light", "English profile comparison hub on mobile"),
    ("/profile-designs/", 1440, "light", "English profile comparison hub on desktop"),
    ("/zh/profile-designs/", 492, "light", "Chinese profile comparison hub on mobile"),
    ("/zh/profile-designs/", 1440, "light", "Chinese profile comparison hub on desktop"),
])


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


def request_target(url, theme):
    """Merge harness parameters into a route that may already have a query."""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["__theme"] = theme
    query["__motion"] = MOTION[0]
    if SCROLLTO[0] is not None:
        query["__scrollto"] = "%g" % SCROLLTO[0]
    return urlunsplit(("", "", parts.path or "/", urlencode(query), parts.fragment))


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
        "http://127.0.0.1:%d%s" % (PORT, request_target(url, theme)),
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
                    help="audit computed type ramps, the 12.8px floor, 44px "
                         "controls, reading measures and viewport overflow")
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
    SCROLLTO[0] = args.scrollto
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
            url_parts = urlsplit(url)
            slug = (url_parts.path.strip("/").replace("/", "-") or "home")
            layout = dict(parse_qsl(url_parts.query)).get("profile-layout")
            if layout:
                slug += "-" + re.sub(r"[^a-z0-9-]+", "-", layout.lower()).strip("-")
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
            if r.get("undersizedTargets"):
                flags.append("%d control(s) below the 44px target"
                             % len(r["undersizedTargets"]))
            if r.get("undersizedFunctional"):
                flags.append("%d functional label(s) below their target"
                             % len(r["undersizedFunctional"]))
            expected_body = max(17.6, min(19.2, 17.04 + r["w"] * 0.0015))
            if abs(r.get("bodyFont", 0) - expected_body) > 0.05:
                flags.append("body %.2fpx differs from %.2fpx target"
                             % (r.get("bodyFont", 0), expected_body))
            expected_sm = max(16.0, min(17.6, 15.44 + r["w"] * 0.0015))
            if abs(r.get("smFont", 0) - expected_sm) > 0.05:
                flags.append("sm %.2fpx differs from %.2fpx target"
                             % (r.get("smFont", 0), expected_sm))
            expected_xs = max(14.4, min(15.2, 14.112 + r["w"] * 0.00075))
            if abs(r.get("xsFont", 0) - expected_xs) > 0.05:
                flags.append("xs %.2fpx differs from %.2fpx target"
                             % (r.get("xsFont", 0), expected_xs))
            if r.get("unboundedReading"):
                flags.append("%d reading block(s) exceed the measure"
                             % len(r["unboundedReading"]))
            if r.get("narrowProjectMedia"):
                flags.append("%d project media block(s) are not full-width"
                             % len(r["narrowProjectMedia"]))
            profile = r.get("profile")
            if profile:
                valid_profile_query = profile.get("requested") in (
                    "editorial", "dossier", "narrative"
                )
                if profile.get("applied") != profile.get("expected"):
                    flags.append("profile applied %s instead of %s"
                                 % (profile.get("applied"), profile.get("expected")))
                if profile.get("compareFlag") != ("true" if valid_profile_query else "false"):
                    flags.append("profile comparison flag disagrees with query validity")
                if not profile.get("switcherVisible"):
                    flags.append("profile switcher is not visible")
                if profile.get("choiceCount") != 3:
                    flags.append("profile switcher does not have exactly three choices")
                expected_active = 1
                if profile.get("activeChoiceCount") != expected_active:
                    flags.append("profile switcher has %s active choices, expected %s"
                                 % (profile.get("activeChoiceCount"), expected_active))
                counts = profile.get("regionCounts", {})
                if any(counts.get(region) != 1 for region in ("identity", "narrative", "record")):
                    flags.append("profile does not contain one identity/narrative/record region")
                for label, actual_key, expected_key in (
                    ("name", "nameFont", "expectedNameFont"),
                    ("role", "roleFont", "expectedRoleFont"),
                    ("narrative", "narrativeFont", "expectedNarrativeFont"),
                    ("section heading", "sectionHeadFont", "expectedSectionHeadFont"),
                    ("fact label", "factLabelFont", "expectedFactLabelFont"),
                    ("fact value", "factValueFont", "expectedFactValueFont"),
                ):
                    if abs(profile.get(actual_key, 0) - profile.get(expected_key, 0)) > 0.05:
                        flags.append("profile %s type %.2fpx differs from %.2fpx token"
                                     % (label, profile.get(actual_key, 0),
                                        profile.get(expected_key, 0)))
                if not profile.get("mobileOrder", True):
                    flags.append("profile mobile order is not name/identity/narrative/facts")
                if profile.get("overlaps"):
                    flags.append("profile regions overlap")
                language_href = profile.get("languageHref", "")
                expected_query = "profile-layout=" + profile.get("expected", "")
                if valid_profile_query and expected_query not in language_href:
                    flags.append("language switch drops the active profile layout")
                if not valid_profile_query and "profile-layout=" in language_href:
                    flags.append("language switch invents a profile layout on a normal visit")
                interaction = profile.get("interaction", {})
                if not interaction.get("tested"):
                    flags.append("profile switcher interaction was not exercised")
                if interaction.get("tested") and not interaction.get("passed"):
                    flags.append("profile switcher did not update and restore the query/layout")
            partners = r.get("partners")
            if r.get("url") in ("/", "/zh/") and not partners:
                flags.append("partner computed audit is missing from a home page")
            elif partners:
                if partners.get("arrowCount") != 0:
                    flags.append("partner arrow elements remain")
                if partners.get("viewportCount") != 2 or partners.get("bandCount") != 2:
                    flags.append("partner strip does not expose exactly two row controls")
                for label, key in (
                    ("named", "namedControls"),
                    ("uniquely named", "uniqueLabels"),
                    ("described", "describedControls"),
                    ("shortcut-labelled", "shortcutControls"),
                    ("tabbable", "tabbableControls"),
                    ("grouped", "groupedControls"),
                ):
                    if not partners.get(key):
                        flags.append("partner rows are not all %s controls" % label)
                if partners.get("rowCount") != 4 or not partners.get("duplicateRowsHidden"):
                    flags.append("partner duplicate rows have incorrect accessibility state")
                if not partners.get("rowWidthsMatch"):
                    flags.append("partner duplicate-row widths do not match")
                if partners.get("logoCount", 0) <= 0:
                    flags.append("partner SVG logos are missing")
                for label, key in (
                    ("free of the reverted frames", "logosUnframed"),
                    ("loaded", "logosLoaded"),
                    ("using the restored filter treatment", "filtersPresent"),
                ):
                    if not partners.get(key):
                        flags.append("partner logos are not all %s" % label)
                partner_keyboard = partners.get("keyboard", {})
                if not partner_keyboard.get("tested"):
                    flags.append("partner keyboard interaction was not exercised")
                elif not partner_keyboard.get("passed"):
                    flags.append("partner Left/Right keys did not visibly move only the focused row")
                if r.get("motion") == "off" and not partner_keyboard.get("motionPaused"):
                    flags.append("partner keyboard test did not run with motion paused")
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
            for x in r.get("undersizedTargets", []):
                print("        target " + x)
            for x in r.get("undersizedFunctional", []):
                print("        label  " + x)
            for x in r.get("unboundedReading", []):
                print("        measure " + x)
            for x in r.get("narrowProjectMedia", []):
                print("        media  " + x)
            if profile:
                print("        profile requested=%s applied=%s switcher=%s interaction=%s"
                      % (profile.get("requested") or "(none)", profile.get("applied"),
                         "shown" if profile.get("switcherVisible") else "hidden",
                         "pass" if profile.get("interaction", {}).get("passed") else "fail"))
            if partners:
                print("        partners rows=%s logos=%s keyboard=%s filters=%s"
                      % (partners.get("viewportCount"), partners.get("logoCount"),
                         "pass" if partners.get("keyboard", {}).get("passed") else "fail",
                         "present" if partners.get("filtersPresent") else "missing"))
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
        if bad:
            return 1

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
