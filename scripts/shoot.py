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
   Motion is selected after load through the real LabMotion API. The harness
   also seeds the obsolete labMotion key to "off" so every shot proves stale
   storage cannot freeze a fresh page. Each launch gets a throwaway
   --user-data-dir, so neither state can leak into the reviewer's own browser.

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
import base64
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cdp  # noqa: E402  (needs the line above to be importable)

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
    if (q.get("__storedmotion")) localStorage.setItem("labMotion", q.get("__storedmotion"));
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

AUDIT = r"""<script>
/* Injected by scripts/shoot.py --measure. Reports the two things a grep over
   style.css cannot see, because both are COMPUTED: the final font-size of
   every element that really renders text, and anything wider than the
   viewport. */
window.addEventListener("load", function () {
  /* A stale saved pause value must never freeze a new page. The audit records
     the production default first, then uses the public API to select the
     current-page state needed by this particular shot. */
  var auditQuery = new URLSearchParams(location.search);
  var motionStartsRunning = !!window.LabMotion && window.LabMotion.isRunning();
  if (window.LabMotion && typeof window.LabMotion.set === "function") {
    window.LabMotion.set(auditQuery.get("__motion") !== "off");
  }
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

  async function measure() {
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
    var small = [], wide = [], undersizedTargets = [], constrainedNotes = [];
    var unjustifiedNotes = [], seen = {};
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
    /* Notes and prose now follow the full-width page-header lead. They may be
       narrowed by an actual grid column, but not by a second max-width cap. */
    var noteWidthSelector = [
      ".section-head", ".page-narrow", ".pi-body", ".pub-theme",
      ".profile-narrative", ".form-col", ".pg-scope",
      ".project-body > h2", ".project-body > h3", ".project-body > h4",
      ".project-body > p:not(:has(img, picture, video))", ".project-body > ul",
      ".project-body > ol", ".project-body > blockquote"
    ].join(",");
    var noteWidths = document.querySelectorAll(noteWidthSelector);
    var noteWidthSeen = {};
    for (var u = 0; u < noteWidths.length; u++) {
      var noteWidthStyle = getComputedStyle(noteWidths[u]);
      if (noteWidthStyle.display === "none" || noteWidthStyle.visibility === "hidden") continue;
      if (noteWidthStyle.maxWidth !== "none") {
        var noteWidthKey = sel(noteWidths[u]);
        if (!noteWidthSeen[noteWidthKey]) {
          noteWidthSeen[noteWidthKey] = 1;
          constrainedNotes.push(noteWidthKey + " max " + noteWidthStyle.maxWidth);
        }
      }
    }
    var noteTextSelector = [
      ".page-hd p:not(.profile-header-summary)", ".section-head p", ".page-narrow p", ".pi-body p",
      ".pub-theme p", ".pub-theme li", ".profile-narrative p",
      ".setup-notes p", ".setup-notes li",
      ".form-col > p", ".pg-scope", ".project-body > p:not(:has(img, picture, video))",
      ".project-body > :is(ul, ol) > li", ".project-body > blockquote"
    ].join(",");
    var noteTexts = document.querySelectorAll(noteTextSelector);
    var justifySeen = {};
    for (var jn = 0; jn < noteTexts.length; jn++) {
      var noteTextStyle = getComputedStyle(noteTexts[jn]);
      if (noteTextStyle.display === "none" || noteTextStyle.visibility === "hidden") continue;
      if (noteTextStyle.textAlign !== "justify") {
        var justifyKey = sel(noteTexts[jn]);
        if (!justifySeen[justifyKey]) {
          justifySeen[justifyKey] = 1;
          unjustifiedNotes.push(justifyKey + " = " + noteTextStyle.textAlign);
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
    var heroTitleAudit = null;
    var heroTitle = document.querySelector(".hero-title");
    if (heroTitle) {
      var heroTitleStyle = getComputedStyle(heroTitle);
      var heroTitleRange = document.createRange();
      heroTitleRange.selectNodeContents(heroTitle);
      var heroLineTops = [];
      Array.prototype.forEach.call(heroTitleRange.getClientRects(), function (rect) {
        var top = Math.round(rect.top * 10) / 10;
        if (heroLineTops.indexOf(top) === -1) heroLineTops.push(top);
      });
      heroTitleAudit = {
        balanced: heroTitleStyle.textWrap === "balance",
        constrained: heroTitleStyle.maxInlineSize !== "none",
        manualBreaks: heroTitle.querySelectorAll("br").length,
        fits: heroTitle.scrollWidth <= heroTitle.clientWidth + 1,
        lines: heroLineTops.length
      };
    }
    var profileShell = document.querySelector(".profile-layout");
    if (profileShell) {
      var profileRequested = new URLSearchParams(location.search).get("profile-layout");
      var profileRoot = document.documentElement;
      var profileName = document.querySelector(".person-hd .pi-heading");
      var profileHeaderIdentity = document.querySelector(".profile-header-identity");
      var profileHeaderPortrait = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".pi-portrait-frame") : null;
      var profileHeaderRule = document.querySelector(".person-hd .pi-rule");
      var profileHeaderDetailsNode = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-header-details") : null;
      var profileHeaderSummary = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-header-summary") : null;
      var profileHeaderRole = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-role") : null;
      var profileHeaderExpertise = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-expertise") : null;
      var profileHeaderExpertiseLabel = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-expertise-label") : null;
      var profileHeaderContacts = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".pi-chips") : null;
      var profileNarrative = profileShell.querySelector(".profile-narrative");
      var profileRecord = profileShell.querySelector(".profile-record");
      var profileRole = profileHeaderIdentity ?
        profileHeaderIdentity.querySelector(".profile-role") : null;
      var profileSectionHead = profileShell.querySelector(".profile-narrative h2");
      var profileFactLabel = profileShell.querySelector(".pf-label");
      var profileFactValue = profileShell.querySelector(".pf-values");
      var profileLanguageHref = document.querySelector(".lang-switch") ?
        document.querySelector(".lang-switch").getAttribute("href") : "";
      var profileRects = [profileHeaderPortrait, profileHeaderSummary,
        profileHeaderContacts, profileNarrative, profileRecord]
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
      if (window.innerWidth <= 991.98) {
        if (profileName && profileHeaderSummary && profileHeaderContacts &&
            profileHeaderPortrait && profileNarrative && profileRecord) {
          var mobileNameRect = profileName.getBoundingClientRect();
          var mobileSummaryRect = profileHeaderSummary.getBoundingClientRect();
          var mobileContactsRect = profileHeaderContacts.getBoundingClientRect();
          var mobilePortraitRect = profileHeaderPortrait.getBoundingClientRect();
          var mobileNarrativeRect = profileNarrative.getBoundingClientRect();
          var mobileRecordRect = profileRecord.getBoundingClientRect();
          profileMobileOrder = mobileNameRect.bottom <= mobileSummaryRect.top + 1 &&
            mobileSummaryRect.bottom <= mobileContactsRect.top + 1 &&
            mobileContactsRect.bottom <= mobilePortraitRect.top + 1 &&
            mobilePortraitRect.bottom <= mobileNarrativeRect.top + 1 &&
            mobileNarrativeRect.bottom <= mobileRecordRect.top + 1;
        } else {
          profileMobileOrder = false;
        }
      }
      var headerDetails = {
        present: true,
        desktopTwoRows: true,
        ruleHidden: true,
        domOrderValid: true,
        expertiseWrapsOnNarrow: true,
        expertiseListSemantics: true,
        expertiseLabelAbsent: true
      };
      headerDetails.present = !!profileHeaderPortrait && !!profileHeaderSummary &&
        !!profileHeaderRole && !!profileHeaderContacts;
      headerDetails.ruleHidden = !!profileHeaderRule &&
        getComputedStyle(profileHeaderRule).display === "none";
      headerDetails.domOrderValid = !!profileHeaderDetailsNode && !!profileHeaderPortrait &&
        !!(profileHeaderDetailsNode.compareDocumentPosition(profileHeaderPortrait) &
           Node.DOCUMENT_POSITION_FOLLOWING);
      var expertiseItems = profileHeaderExpertise ?
        profileHeaderExpertise.querySelectorAll('[role="listitem"]') : [];
      headerDetails.expertiseListSemantics = !profileHeaderExpertise ||
        (profileHeaderExpertise.getAttribute("role") === "list" &&
         expertiseItems.length >= 1);
      headerDetails.expertiseLabelAbsent = !profileHeaderExpertiseLabel;
      if (profileHeaderExpertise && window.innerWidth <= 991.98) {
        var expertiseStyle = getComputedStyle(profileHeaderExpertise);
        headerDetails.expertiseWrapsOnNarrow = expertiseStyle.flexWrap === "wrap" &&
          expertiseStyle.minWidth === "0px" &&
          profileHeaderExpertise.scrollWidth <= profileHeaderExpertise.clientWidth + 1;
      }
      if (headerDetails.present && window.innerWidth > 991.98) {
        var headerNameRect = profileName.getBoundingClientRect();
        var headerPortraitRect = profileHeaderPortrait.getBoundingClientRect();
        var headerSummaryRect = profileHeaderSummary.getBoundingClientRect();
        var headerContactsRect = profileHeaderContacts.getBoundingClientRect();
        var headerRoleRect = profileHeaderRole.getBoundingClientRect();
        var headerContactLinks = profileHeaderContacts.querySelectorAll(".pi-chip");
        var contactTop = headerContactLinks.length ?
          headerContactLinks[0].getBoundingClientRect().top : headerContactsRect.top;
        var contactsShareRow = Array.prototype.every.call(headerContactLinks, function (link) {
          return Math.abs(link.getBoundingClientRect().top - contactTop) <= 1;
        });
        var expertiseRect = profileHeaderExpertise ?
          profileHeaderExpertise.getBoundingClientRect() : null;
        var expertiseSharesRow = !expertiseRect ||
          Math.min(expertiseRect.bottom, headerRoleRect.bottom) -
            Math.max(expertiseRect.top, headerRoleRect.top) > 1;
        headerDetails.desktopTwoRows =
          headerSummaryRect.top >= headerNameRect.bottom - 1 &&
          Math.abs(headerSummaryRect.left - headerNameRect.left) <= 2 &&
          headerContactsRect.top >= headerSummaryRect.bottom - 1 &&
          Math.abs(headerContactsRect.left - headerNameRect.left) <= 2 &&
          headerPortraitRect.left > headerSummaryRect.left &&
          headerPortraitRect.top <= headerSummaryRect.top &&
          expertiseSharesRow && contactsShareRow;
      }
      profileAudit = {
        requested: profileRequested || "",
        layoutStateAbsent: !profileRoot.hasAttribute("data-profile-layout") &&
          !profileRoot.hasAttribute("data-profile-layout-compare"),
        switcherAbsent: !document.querySelector("[data-profile-switcher]") &&
          !document.querySelector("[data-profile-layout-choice]"),
        controllerAbsent: !document.querySelector('script[src*="profile-layout.js"]'),
        regionCounts: {
          identity: profileShell.querySelectorAll(".profile-identity").length,
          headerIdentity: document.querySelectorAll(".profile-header-identity").length,
          narrative: profileShell.querySelectorAll(".profile-narrative").length,
          record: profileShell.querySelectorAll(".profile-record").length
        },
        identityLocationValid: !!profileHeaderIdentity &&
          getComputedStyle(profileHeaderIdentity).display !== "none" &&
          !!profileHeaderIdentity.closest(".person-hd"),
        headerPortraitWidth: profileHeaderIdentity ?
          profileHeaderIdentity.querySelector(".pi-portrait-frame").getBoundingClientRect().width : 0,
        headerIdentityInsideHeader: !!profileHeaderIdentity &&
          !!profileHeaderIdentity.closest(".person-hd"),
        headerDetails: headerDetails,
        nameFont: profileName ? parseFloat(getComputedStyle(profileName).fontSize) : 0,
        expectedNameFont: tokenSize("--fs-3xl"),
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
        overlaps: profileOverlap
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
      var logoPointerEventsRestored = true;
      for (var pl = 0; pl < partnerLogos.length; pl++) {
        var logo = partnerLogos[pl];
        var logoFrame = logo.closest(".pt-logo-frame");
        logosUnframed = logosUnframed && !logoFrame;
        logosLoaded = logosLoaded && logo.complete && logo.naturalWidth > 0;
        filtersPresent = filtersPresent && getComputedStyle(logo).filter !== "none";
        logoPointerEventsRestored = logoPointerEventsRestored &&
          getComputedStyle(logo).pointerEvents === "auto";
      }
      var partnerKeyboard = { tested: false, passed: false, motionPaused: false };
      var partnerMotion = { expected: false, moving: false, resumesAfterDrag: false };
      var partnerFocus = { borderless: false, lineCue: false };
      if (window.__partners && window.__partners.bands &&
          window.__partners.bands.length === 2 && partnerViewports.length === 2) {
        partnerMotion.expected = !!window.LabMotion &&
          typeof window.LabMotion.isRunning === "function" &&
          window.LabMotion.isRunning();
        partnerMotion.moving = !partnerMotion.expected ||
          window.__partners.bands.every(function (band) {
            return band.speed !== 0 && band.pos !== 0 &&
              band.track.style.transform && band.track.style.transform !== "none";
          });
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
        var viewportFocusStyle = getComputedStyle(partnerViewports[1]);
        var bandFocusCue = getComputedStyle(partnerBands[1], "::after");
        var viewportShadow = viewportFocusStyle.boxShadow;
        var visibleViewportShadow = viewportShadow !== "none" &&
          viewportShadow.indexOf("rgba(0, 0, 0, 0)") === -1 &&
          !/0px 0px 0px 0px(?:$|,)/.test(viewportShadow);
        partnerFocus.borderless = viewportFocusStyle.outlineStyle === "none" &&
          !visibleViewportShadow;
        partnerFocus.lineCue = parseFloat(bandFocusCue.height) <= 4 &&
          bandFocusCue.backgroundColor !== "rgba(0, 0, 0, 0)";
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
        partnerMotion.resumesAfterDrag = window.__partners.bands.every(function (band) {
          return !band.dragging && band.pointerId === null && Number.isFinite(band.baseTime);
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
        logoPointerEventsRestored: logoPointerEventsRestored,
        keyboard: partnerKeyboard,
        motion: partnerMotion,
        focus: partnerFocus
      };
    }
    var setupImages = Array.prototype.slice.call(
      document.querySelectorAll(".fig-media img"));
    await Promise.all(setupImages.map(function (setupImage) {
      if (setupImage.complete) return Promise.resolve();
      return new Promise(function (resolve) {
        var settled = false;
        function finish() {
          if (settled) return;
          settled = true;
          clearTimeout(timer);
          resolve();
        }
        var timer = setTimeout(finish, 1500);
        setupImage.addEventListener("load", finish, { once: true });
        setupImage.addEventListener("error", finish, { once: true });
      });
    }));
    await Promise.all(setupImages.map(function (setupImage) {
      if (!setupImage.complete || !setupImage.naturalWidth ||
          typeof setupImage.decode !== "function") return Promise.resolve();
      return Promise.race([
        setupImage.decode().catch(function () {}),
        new Promise(function (resolve) { setTimeout(resolve, 750); })
      ]);
    }));
    var setupImageIssues = [];
    var setupImagesLoaded = 0;
    for (var si = 0; si < setupImages.length; si++) {
      var setupImage = setupImages[si];
      var setupImageSrc = setupImage.getAttribute("src") || "(unknown image)";
      var setupImageRect = setupImage.getBoundingClientRect();
      if (!setupImage.complete || !setupImage.naturalWidth ||
          !setupImage.naturalHeight || !setupImageRect.width ||
          !setupImageRect.height) {
        setupImageIssues.push(setupImageSrc + " did not load to measurable dimensions");
        continue;
      }
      setupImagesLoaded++;
      var setupImageStyle = getComputedStyle(setupImage);
      var naturalRatio = setupImage.naturalWidth / setupImage.naturalHeight;
      var renderedRatio = setupImageRect.width / setupImageRect.height;
      var fit = setupImageStyle.objectFit;
      var containScale = Math.min(
        setupImageRect.width / setupImage.naturalWidth,
        setupImageRect.height / setupImage.naturalHeight);
      var paintedWidth = setupImageRect.width;
      var paintedHeight = setupImageRect.height;
      if (fit === "contain") {
        paintedWidth = setupImage.naturalWidth * containScale;
        paintedHeight = setupImage.naturalHeight * containScale;
      } else if (fit === "cover") {
        var coverScale = Math.max(
          setupImageRect.width / setupImage.naturalWidth,
          setupImageRect.height / setupImage.naturalHeight);
        paintedWidth = setupImage.naturalWidth * coverScale;
        paintedHeight = setupImage.naturalHeight * coverScale;
      } else if (fit === "none") {
        paintedWidth = setupImage.naturalWidth;
        paintedHeight = setupImage.naturalHeight;
      } else if (fit === "scale-down") {
        var scaleDown = Math.min(1, containScale);
        paintedWidth = setupImage.naturalWidth * scaleDown;
        paintedHeight = setupImage.naturalHeight * scaleDown;
      }
      var distorted = fit === "fill" &&
        Math.abs(renderedRatio - naturalRatio) / naturalRatio > 0.01;
      var croppedByFit = paintedWidth > setupImageRect.width + 1 ||
        paintedHeight > setupImageRect.height + 1;
      var clippedByAncestor = false;
      for (var clipNode = setupImage.parentElement;
           clipNode && clipNode !== setupImage.closest(".fig");
           clipNode = clipNode.parentElement) {
        var clipStyle = getComputedStyle(clipNode);
        if (!/(hidden|clip|scroll|auto)/.test(
              clipStyle.overflowX + " " + clipStyle.overflowY)) continue;
        var clipRect = clipNode.getBoundingClientRect();
        if (setupImageRect.left < clipRect.left - 1 ||
            setupImageRect.right > clipRect.right + 1 ||
            setupImageRect.top < clipRect.top - 1 ||
            setupImageRect.bottom > clipRect.bottom + 1) {
          clippedByAncestor = true;
          break;
        }
      }
      if (distorted || croppedByFit || clippedByAncestor) {
        setupImageIssues.push(
          setupImageSrc + " fit=" + fit +
          " natural/rendered=" + naturalRatio.toFixed(3) + "/" +
          renderedRatio.toFixed(3) +
          " painted/box=" + paintedWidth.toFixed(1) + "x" +
          paintedHeight.toFixed(1) + "/" + setupImageRect.width.toFixed(1) +
          "x" + setupImageRect.height.toFixed(1) +
          " ancestor-clipped=" + clippedByAncestor
        );
      }
    }
    var setupImageAudit = {
      total: setupImages.length,
      loaded: setupImagesLoaded,
      issues: setupImageIssues.slice(0, 12)
    };
    /* ------------------------------------------------------------------
       THE READING MEASURE, IN REAL CHARACTERS PER LINE.

       Justification is required everywhere on this site and nothing has ever
       checked whether the column is wide enough to carry it. style.css names
       the floor itself, at the .foot-addr note: below about 45 characters the
       word spaces measured 14-16px against 3-4px on the last line and a river
       ran down the block.

       Characters per line is counted from the TEXT, not guessed from a font
       size. A Range over the contents returns one client rect per line box, so
       distinct rect tops are the line count, and length/lines is the measure a
       reader actually sees.
       ------------------------------------------------------------------ */
    var justifyAudit = [], justifyAuditSeen = {};
    var proseNodes = document.querySelectorAll(
      "p, li, blockquote, .card-scope, .pg-scope, .person-row-topic, .news-body");
    for (var pj = 0; pj < proseNodes.length; pj++) {
      var proseNode = proseNodes[pj];
      var proseStyle = getComputedStyle(proseNode);
      if (proseStyle.display === "none" || proseStyle.visibility === "hidden") continue;
      if (proseStyle.textAlign !== "justify") continue;
      var proseText = (proseNode.textContent || "").replace(/\s+/g, " ").trim();
      if (proseText.length < 60) continue;
      var proseRange = document.createRange();
      proseRange.selectNodeContents(proseNode);
      var proseRects = proseRange.getClientRects(), tops = [];
      for (var pr = 0; pr < proseRects.length; pr++) {
        if (proseRects[pr].width > 0) tops.push(proseRects[pr].top);
      }
      /* CLUSTER the tops, never round them. An inline <strong> or <a> sits a
         fraction of a pixel off its own line, and rounding turns that into a
         second line, which makes a wide paragraph look like a narrow one. */
      tops.sort(function (a, b) { return a - b; });
      var proseLines = 0, lastTop = -1e9;
      for (var tp = 0; tp < tops.length; tp++) {
        if (tops[tp] - lastTop > 3) { proseLines++; lastTop = tops[tp]; }
      }
      if (proseLines < 2) continue;
      var proseKey = sel(proseNode);
      if (justifyAuditSeen[proseKey]) continue;
      justifyAuditSeen[proseKey] = 1;
      /* The honest characters-per-line is the BOX width over the average
         character width, not the text length over the line count. Every line
         but the last is stretched to the box, and the last line is usually
         short, so length/lines always reads low. The average is measured from
         this element's own text in its own computed font. */
      var widthProbe = document.createElement("span");
      widthProbe.style.cssText = "position:absolute;left:-99999px;top:0;white-space:pre;";
      widthProbe.style.fontFamily = proseStyle.fontFamily;
      widthProbe.style.fontSize = proseStyle.fontSize;
      widthProbe.style.fontWeight = proseStyle.fontWeight;
      widthProbe.style.fontStyle = proseStyle.fontStyle;
      widthProbe.style.letterSpacing = proseStyle.letterSpacing;
      widthProbe.textContent = proseText.slice(0, 400);
      document.body.appendChild(widthProbe);
      var avgChar = widthProbe.getBoundingClientRect().width /
                    Math.max(1, widthProbe.textContent.length);
      document.body.removeChild(widthProbe);
      var proseBox = proseNode.getBoundingClientRect().width;
      justifyAudit.push({
        sel: proseKey,
        px: +proseBox.toFixed(1),
        chars: proseText.length, lines: proseLines,
        cpl: avgChar > 0 ? +(proseBox / avgChar).toFixed(1) : 0,
        cplNaive: +(proseText.length / proseLines).toFixed(1),
        avgChar: +avgChar.toFixed(2),
        font: +parseFloat(proseStyle.fontSize).toFixed(1)
      });
    }

    /* ------------------------------------------------------------------
       THE SETUP GRID, AS THE BROWSER RESOLVED IT.

       gridTemplateColumns comes back as used pixel values, so this reports
       what the figure track really is rather than what the stylesheet asked
       for. That is the only way to see a four-column track holding two
       figures, which reads as a broken row and cannot be found by grepping.
       ------------------------------------------------------------------ */
    /* ------------------------------------------------------------------
       THE ROW AUDIT.

       A justified row gives every picture in it `flex: aspect 1 0`, so the
       widths come out proportional to aspect and every height is the same
       number. Two things can go wrong and neither is visible in a
       screenshot at a glance:

         heightSpread  the heights are NOT equal. Some rule has overridden
                       the computed size, and the row is a plain flex line
                       wearing the class of a justified one. A min-height on
                       a figure did exactly this and was removed.

         upscaled      a picture is painted wider than its own pixels. The
                       cap that prevents it lives on the ROW's max-width,
                       computed from the smallest natural height in the row,
                       and one wrong figure size in _data/ would break it
                       silently.
       ------------------------------------------------------------------ */
    var figRows = [];
    var rowNodes = document.querySelectorAll(".fig-row");
    for (var rw = 0; rw < rowNodes.length; rw++) {
      var rowNode = rowNodes[rw];
      var rowRect = rowNode.getBoundingClientRect();
      var items = rowNode.querySelectorAll(".fig");
      var heights = [], upscaled = [], itemList = [];
      for (var it = 0; it < items.length; it++) {
        var itemImg = items[it].querySelector("img");
        if (!itemImg) continue;
        var itemRect = itemImg.getBoundingClientRect();
        if (!itemRect.width || !itemImg.naturalWidth) continue;
        /* The spread is measured on the MEDIA BOX, not on the image inside
           it. A diagram's box carries padding so its drawing does not touch
           the frame, which makes its image 33.6px shorter than a photograph
           beside it at 1440 while the two boxes are exactly level. Measuring
           the image reported a 33.59px spread on seven pages that were in
           fact perfectly justified. The box is what the eye lines up. */
        var itemBox = items[it].querySelector(".fig-media");
        heights.push((itemBox || itemImg).getBoundingClientRect().height);
        if (itemRect.width > itemImg.naturalWidth * 1.05) {
          upscaled.push((itemImg.getAttribute("src") || "?").split("/").pop() +
            " " + Math.round(itemRect.width) + "px of " + itemImg.naturalWidth);
        }
        itemList.push({
          src: (itemImg.getAttribute("src") || "?").split("/").pop(),
          w: +itemRect.width.toFixed(1), h: +itemRect.height.toFixed(1),
          natW: itemImg.naturalWidth
        });
      }
      figRows.push({
        n: items.length,
        stacked: getComputedStyle(rowNode).display !== "flex",
        rowPx: +rowRect.width.toFixed(1),
        spread: heights.length ?
          +(Math.max.apply(null, heights) - Math.min.apply(null, heights)).toFixed(2) : 0,
        upscaled: upscaled,
        figs: itemList
      });
    }

    fetch("/__report", { method: "POST", body: JSON.stringify({
      url: location.pathname, w: window.innerWidth,
      motionStartsRunning: motionStartsRunning,
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
      constrainedNotes: constrainedNotes.slice(0, 12),
      unjustifiedNotes: unjustifiedNotes.slice(0, 12),
      narrowProjectMedia: narrowProjectMedia.slice(0, 8),
      overflowing: wide.slice(0, 14), heroTitle: heroTitleAudit,
      profile: profileAudit, partners: partnerAudit,
      setupImages: setupImageAudit,
      justifyAudit: justifyAudit, figRows: figRows
    })});
  }
});
</script>"""

REPORTS = []
MOTION = ["off"]    # set from --motion; a list so shoot() can read it
SCROLLTO = [None]   # set from --scrollto
REALTIME = [False]  # set from --realtime
EMULATE = [False]   # set from --emulate; drives shoot_cdp instead of shoot
BROWSER = [None]    # the one reusable CDP browser, in --emulate runs only
WIDTH_MISSES = []   # (url, asked, got) where content would not fit
NO_SHOTS = [False]  # set from --no-shots; measure without capturing

# page, width, theme, why this shot exists
MATRIX = [
    ("/", 492, "light", "bottom of the fluid ramp: hero at the clamp minimum, stacked buttons"),
    ("/", 768, "light", "the 991.98 block with the 767.98 block off, cards 2-up"),
    ("/", 1440, "light", "the reference shot"),
    ("/", 1920, "light", "top of the ramp: hero at the clamp maximum, full-width notes holding"),
    ("/", 492, "dark", "dark tokens at the narrow end"),
    ("/", 1440, "dark", "dark parity: diff against the 1440 light shot, only colour should move"),
    ("/projects/", 492, "light", "filter chips and project cards at the narrow end"),
    ("/projects/", 1440, "light", "project list and filters at the reference width"),
    ("/projects/", 1440, "dark", "project list theme parity"),
    ("/projects/two-phase-closed-loop-thermosyphon/", 1440, "light",
     "imported project figures preserve their complete source image"),
    ("/facilities/thermal-fin-natural-convection-chamber/", 1440, "light",
     "single-figure layout A must not reserve an empty media column"),
    ("/facilities/thermal-fin-natural-convection-chamber/", 492, "light",
     "single-figure layout A must retain the mobile stack"),
    ("/facilities/air-cooler-wind-tunnel/", 492, "light",
     "single-figure layout B must use the full mobile media width"),
    ("/projects/thermosyphon-working-fluid-filling-ratio/", 492, "light",
     "single-figure layout C must use the full mobile media width"),
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
]

# Every real profile uses the selected header identity. The desktop cross-
# product catches language- or theme-scoped regressions without retaining the
# archived A/B/C comparison matrix.
for language, prefix in (("English", "/"), ("Chinese", "/zh/")):
    for person in ("cc-wang", "maysam-gholampour"):
        for theme in ("light", "dark"):
            MATRIX.append((
                f"{prefix}people/{person}/",
                1440,
                theme,
                f"{language} {person} selected header profile",
            ))

for language, prefix in (("English", "/"), ("Chinese", "/zh/")):
    for person in ("cc-wang", "maysam-gholampour"):
        MATRIX.append((
            f"{prefix}people/{person}/",
            492,
            "light",
            f"{language} {person} selected header profile on mobile",
        ))

MATRIX.append((
    "/people/cc-wang/?profile-layout=editorial",
    492,
    "light",
    "legacy profile-layout query is ignored and still renders the selected design",
))


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
    query["__storedmotion"] = "off"
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


def setup_routes():
    """Every public facility and project detail route, read from _data/.

    Generated, never listed by hand. A record added to facilities.toml or
    projects.toml is swept on the next run with no edit here, which is the
    same rule the rest of the site follows: the data file is the source and
    the page grows itself.
    """
    import tomllib
    routes = []
    for name, key, base in (("facilities.toml", "item", "/facilities/"),
                            ("projects.toml", "project", "/projects/")):
        with open(ROOT / "_data" / name, "rb") as fh:
            rows = tomllib.load(fh)[key]
        for row in rows:
            if row.get("placeholder", False):
                continue
            routes.append((base + row["id"] + "/", len(row.get("figure", [])),
                           str(row.get("layout", "-"))))
    return routes


def setup_matrix(widths, theme="light"):
    out = []
    for route, figures, layout in setup_routes():
        for w in widths:
            out.append((route, w, theme,
                        "layout %s, %d figure(s)" % (layout, figures)))
    return out


def shoot_cdp(edge, url, width, theme, out_png, profile, height=4000):
    """Shoot at a TRUE layout width, over CDP. See scripts/cdp.py for why.

    Three things differ from shoot() above, and all three are improvements:

      1. The width is real. `Emulation.setDeviceMetricsOverride` sets the
         layout viewport, so 320 is 320. shoot() cannot go below about 484 and
         crops the difference, which is why NARROWEST exists.
      2. There is no virtual-time budget, so requestAnimationFrame FIRES.
         Point 4 of the module docstring says scroll-linked effects cannot be
         measured; that is a limit of the --screenshot= flag, which shoots at
         load and exits. Here the screenshot is a protocol call, so the page
         can be given real time first and rAF works.
      3. One browser serves the whole run instead of one process per shot.

    The width is ASSERTED, not assumed. A harness that quietly lays out at the
    wrong width is the exact fault this file was written to remove, so a
    mismatch fails the shot rather than writing a mislabelled PNG.
    """
    browser = BROWSER[0]
    if browser is None:
        browser = cdp.Browser(edge, profile)
        browser.call("Page.enable")
        browser.call("Runtime.enable")
        BROWSER[0] = browser

    browser.call("Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1,
        "mobile": width < 768, "screenWidth": width, "screenHeight": height,
    })
    before = len(REPORTS)
    browser.clear_events()
    browser.call("Page.navigate", {
        "url": "http://127.0.0.1:%d%s" % (PORT, request_target(url, theme))})
    browser.await_event("Page.loadEventFired", timeout=90)

    seen = browser.evaluate("window.innerWidth")
    if seen != width:
        # This is a FINDING, not a harness fault, and the picture is the whole
        # point of having it. A page whose content will not fit makes Chromium
        # widen the visual viewport to show it, so innerWidth comes back larger
        # than the device width. Refusing the shot would hide the one page that
        # most needs looking at, so it is recorded and shot anyway.
        WIDTH_MISSES.append((url, width, seen))
        print("      OVERFLOW: content forced the viewport to %spx at %dpx"
              % (seen, width))

    if Injector.measure:
        # The probe fires 2.5 s after load and POSTs to /__report. Poll for it
        # rather than sleeping a guessed amount.
        end = time.monotonic() + 45
        while len(REPORTS) == before and time.monotonic() < end:
            time.sleep(0.1)
        if len(REPORTS) == before:
            print("      the audit probe never reported - shot refused")
            return False
    else:
        time.sleep(1.2)

    if NO_SHOTS[0]:
        return True
    shot = browser.call("Page.captureScreenshot", {"format": "png"}, timeout=180)
    if out_png.exists():
        out_png.unlink()
    out_png.write_bytes(base64.b64decode(shot["data"]))
    return out_png.stat().st_size > 0


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
                    help="set the current-page LabMotion state. Default off, "
                         "which freezes the marquee and slider so shots are "
                         "diffable. Use on to test automatic motion.")
    ap.add_argument("--sweep", choices=["setup"],
                    help="replace the regression matrix with every public "
                         "facility and project detail route, read from _data/")
    ap.add_argument("--widths", default="320,390,1440",
                    help="comma-separated widths for --sweep")
    ap.add_argument("--no-shots", action="store_true",
                    help="run the audit probe but write no PNG. Measurement "
                         "iterates far faster than full-page capture.")
    ap.add_argument("--emulate", action="store_true",
                    help="drive Edge over CDP and set the LAYOUT viewport, so "
                         "widths below 492 are real instead of cropped")
    ap.add_argument("--measure", action="store_true",
                    help="audit computed type ramps, the 12.8px floor, 44px "
                         "controls, reading measures and viewport overflow")
    args = ap.parse_args()

    if args.emulate and args.realtime:
        sys.exit("--emulate already runs in real time and controls when the "
                 "screenshot is taken, so --realtime adds nothing and its "
                 "shoot-at-load behaviour would break the audit.")
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
    EMULATE[0] = args.emulate
    NO_SHOTS[0] = args.no_shots
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

    if args.sweep == "setup":
        shots = setup_matrix([int(w) for w in args.widths.split(",")], args.theme)
    elif args.url:
        shots = [(args.url, args.width, args.theme, "ad hoc")]
    else:
        shots = MATRIX
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
            real = width if args.emulate else max(width, NARROWEST)
            png = OUT / ("%02d_%s_%d_%s.png" % (i, slug, real, theme))
            profile = OUT / ("profile-%02d" % i)
            ok = (shoot_cdp(edge, url, width, theme, png, OUT / "profile-cdp",
                            args.height) if args.emulate else
                  shoot(edge, url, width, theme, png, profile, args.height))
            kb = (png.stat().st_size // 1024
                  if ok and png.is_file() else 0)
            print("  %s %-28s %5d %-5s %6d KB  %s"
                  % ("ok  " if ok else "FAIL", url, width, theme, kb, why))
            (made if ok else failed).append(str(png))
    finally:
        if BROWSER[0] is not None:
            BROWSER[0].close()
            BROWSER[0] = None
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

    if WIDTH_MISSES:
        print("\n=== PAGES THAT WOULD NOT FIT ===")
        for miss_url, asked, got in WIDTH_MISSES:
            print("  %-56s asked %d, laid out %d (+%d)"
                  % (miss_url, asked, got, got - asked))
    if args.measure and REPORTS:
        (OUT / "reports.json").write_text(json.dumps(REPORTS, indent=1),
                                          encoding="utf-8")
        print("\nwrote %s (%d report(s))" % (OUT / "reports.json", len(REPORTS)))
    if args.measure:
        print("\n=== COMPUTED AUDIT ===")
        if not args.no_shots and len(REPORTS) < len(made):
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
            if r.get("constrainedNotes"):
                flags.append("%d note block(s) retain a max-width cap"
                             % len(r["constrainedNotes"]))
            if r.get("unjustifiedNotes"):
                flags.append("%d note block(s) are not justified"
                             % len(r["unjustifiedNotes"]))
            if r.get("narrowProjectMedia"):
                flags.append("%d project media block(s) are not full-width"
                             % len(r["narrowProjectMedia"]))
            # Every page must have composed at least one row, and every row
            # must hold its two invariants. `spread` above 1px means the
            # heights are not equal, which means the justification is not
            # working however plausible the row looks.
            fig_rows = r.get("figRows")
            if not fig_rows:
                flags.append("no justified figure row on the page")
            for i, row in enumerate(fig_rows or (), start=1):
                if not row.get("stacked") and row.get("spread", 0) > 1:
                    flags.append("row %d of %d: heights differ by %.2fpx; the row is "
                                 "not justified" % (i, len(fig_rows), row["spread"]))
                if row.get("upscaled"):
                    flags.append("row %d: %s painted above natural width"
                                 % (i, "; ".join(row["upscaled"])))
            setup_images = r.get("setupImages")
            expected_image_count = sum(row.get("n", 0) for row in fig_rows or ())
            if expected_image_count:
                if not setup_images:
                    flags.append("setup image audit did not run")
                elif setup_images.get("total") != expected_image_count:
                    flags.append("setup image count %s differs from the %s figures "
                                 "the rows contain"
                                 % (setup_images.get("total"), expected_image_count))
                elif setup_images.get("loaded") != expected_image_count:
                    flags.append("only %s/%s setup images loaded"
                                 % (setup_images.get("loaded"), expected_image_count))
            if setup_images and setup_images.get("issues"):
                flags.append("%d setup image(s) are distorted, cropped, clipped, or unloaded"
                             % len(setup_images["issues"]))
            profile = r.get("profile")
            if profile:
                if not profile.get("layoutStateAbsent"):
                    flags.append("retired profile layout state remains on the document")
                if not profile.get("switcherAbsent"):
                    flags.append("retired profile switcher remains")
                if not profile.get("controllerAbsent"):
                    flags.append("retired profile layout controller remains")
                counts = profile.get("regionCounts", {})
                if counts.get("identity") != 0:
                    flags.append("profile retains a duplicate body identity")
                if any(counts.get(region) != 1 for region in ("narrative", "record")):
                    flags.append("profile does not contain one narrative/record region")
                if counts.get("headerIdentity") != 1:
                    flags.append("profile does not contain one header identity")
                if not profile.get("identityLocationValid"):
                    flags.append("profile identity is not visible inside the header")
                if profile.get("headerPortraitWidth", 9999) > 180.5:
                    flags.append("profile portrait exceeds the 180px target")
                if not profile.get("headerIdentityInsideHeader"):
                    flags.append("profile identity is not inside the profile header")
                header_details = profile.get("headerDetails", {})
                if not header_details.get("present"):
                    flags.append("profile role/contact rows are missing")
                if not header_details.get("desktopTwoRows"):
                    flags.append("profile details are not two rows beneath the name")
                if not header_details.get("ruleHidden"):
                    flags.append("profile title accent rule is still visible")
                if not header_details.get("domOrderValid"):
                    flags.append("profile DOM does not order details before portrait")
                if not header_details.get("expertiseWrapsOnNarrow"):
                    flags.append("profile expertise cannot wrap safely on narrow screens")
                if not header_details.get("expertiseListSemantics"):
                    flags.append("profile expertise lacks list semantics")
                if not header_details.get("expertiseLabelAbsent"):
                    flags.append("profile still displays the Expertise in label")
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
                if "profile-layout=" in language_href:
                    flags.append("language switch preserves the retired profile layout query")
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
                    ("using the branch-start pointer behavior", "logoPointerEventsRestored"),
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
                partner_motion = partners.get("motion", {})
                if r.get("motion") == "on" and not partner_motion.get("moving"):
                    flags.append("partner rows do not move automatically when motion is on")
                if not partner_motion.get("resumesAfterDrag"):
                    flags.append("partner rows cannot resume from a completed drag state")
                partner_focus = partners.get("focus", {})
                if not partner_focus.get("borderless"):
                    flags.append("partner row keyboard focus still draws a rectangle")
                if not partner_focus.get("lineCue"):
                    flags.append("partner row keyboard focus lacks a non-rectangular line cue")
            hero_title = r.get("heroTitle")
            if r.get("url") in ("/", "/zh/") and not hero_title:
                flags.append("hero headline computed audit is missing")
            elif hero_title:
                if not hero_title.get("balanced"):
                    flags.append("hero headline does not use balanced wrapping")
                if not hero_title.get("constrained"):
                    flags.append("hero headline has no content-independent line measure")
                if hero_title.get("manualBreaks"):
                    flags.append("hero headline contains manual line breaks")
                if not hero_title.get("fits"):
                    flags.append("hero headline overflows its text rail")
            if over > 1:
                flags.append("page %dpx wider than the viewport" % over)
            if not r["etbook"]:
                flags.append("ET BOOK DID NOT LOAD")
            if not r["loaded"]:
                flags.append("body.loaded never set")
            if not r.get("motionStartsRunning"):
                flags.append("a stale saved pause prevents motion on a fresh page load")
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
            for x in r.get("constrainedNotes", []):
                print("        width  " + x)
            for x in r.get("unjustifiedNotes", []):
                print("        align  " + x)
            for x in r.get("narrowProjectMedia", []):
                print("        media  " + x)
            for i, row in enumerate(r.get("figRows") or (), start=1):
                print("        row %d  n=%s %s%.0fpx spread=%.2f  %s"
                      % (i, row.get("n"), "stacked " if row.get("stacked") else "",
                         row.get("rowPx", 0), row.get("spread", 0),
                         " ".join("%s %.0f/%s" % (f["src"], f["w"], f["natW"])
                                  for f in row.get("figs", []))))
            if setup_images and setup_images.get("total"):
                print("        images loaded/total = %s/%s"
                      % (setup_images.get("loaded"), setup_images.get("total")))
                for x in setup_images.get("issues", []):
                    print("        image  " + x)
            if profile:
                print("        profile requested=%s state=%s switcher=%s"
                      % (profile.get("requested") or "(none)",
                         "absent" if profile.get("layoutStateAbsent") else "present",
                         "absent" if profile.get("switcherAbsent") else "present"))
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
    print("Reminder: clear localStorage labTheme in your OWN browser if you have "
          "been testing themes there by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
