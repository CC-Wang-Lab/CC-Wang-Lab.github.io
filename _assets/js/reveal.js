/*
 * Scroll effects, on every page.
 *
 * Three of them, all cheap, all transform/opacity only so they stay on the
 * compositor:
 *
 *   1. REVEAL   blocks rise 1.25rem and fade in as they come into view,
 *               staggered across a row so a grid arrives left to right.
 *   2. HERO     the home-page hero text drifts up slower than the page and
 *               fades as it leaves, so the video reads as further away.
 *   3. PROGRESS a 2px bar under the navbar showing how far down the page you
 *               are. Long pages here have no other sense of scale.
 *
 * The values are not invented. They come from the same family already measured
 * off imec.com and written down in .claude/rules/animation.md: the card lift is
 * translateY(-1.25em) over .25s ease-out, and the news slider cross-fades over
 * .5s ease-out. A reveal that rises 1.25rem over .55s ease-out is the mirror of
 * the lift, in the same vocabulary.
 *
 * THE ONE RULE THIS FILE MUST NOT BREAK
 * ------------------------------------
 * Everything here obeys window.LabMotion, the single pause control. Pause it
 * and every element is shown immediately, at its final position, with the
 * observers disconnected and the scroll handler removed. Motion off must never
 * mean content hidden. That is the trap .claude/rules/animation.md exists to
 * prevent, and a reveal effect is the easiest possible way to fall into it.
 *
 * prefers-reduced-motion is deliberately not consulted, for the reasons set out
 * at length in motion.js. The pause button is the mechanism.
 *
 * FOUR FAILSAFES, because this file can hide content
 * --------------------------------------------------
 *   a. The CSS only hides elements carrying data-reveal, and only this script
 *      ever sets that attribute. If the script does not run, nothing is hidden.
 *   b. No IntersectionObserver -> reveal everything at once and stop.
 *   c. A 4 s timer reveals anything still hidden, whatever went wrong.
 *   d. Anything already inside the viewport is marked done BEFORE anything is
 *      hidden, so the top of the page is never blank and pressing play halfway
 *      down a page never blinks the block you are reading.
 */
(function () {
  "use strict";

  /* Blocks worth revealing. All of these already exist in the markup, so this
     needs no change to utils.jl and no change to any .md file. */
  var TARGETS = [
    ".section-head",
    ".card-media",
    ".cap-card",
    ".cap-list",
    ".sector",
    ".person-card",
    ".pi-block",
    ".person-row",
    ".news-card",
    ".pub",
    ".year-head",
    ".pub-theme",
    ".pg-item",
    ".project-filter",
    ".contact-card",
    ".contact-form",
    ".band-cta .container",
    /* Headings only inside prose. Fading in the paragraphs of a text page
       means the reader looks at where the words should be and finds nothing,
       which is a worse page, not a fancier one. */
    ".prose > h2",
    ".prose > hr",
    ".pt-head"
  ].join(",");

  /* The stagger STEP is in the CSS, on --reveal-i. This is only the cap, so a
     row of ten cards never makes the last one wait ten steps. */
  var STAGGER_MAX = 5;
  var FAILSAFE_MS = 4000;

  var observer = null;
  var revealed = false;
  var onScroll = null;
  var raf = 0;

  function all(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /** Failsafe (a) and the pause path: show everything, immediately, for good. */
  function revealEverything() {
    if (revealed) return;
    revealed = true;
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    all("[data-reveal]").forEach(function (el) {
      el.setAttribute("data-reveal", "done");
      el.classList.add("is-in");
    });
  }

  /* ---------------------------------------------------------------- reveal */

  function startReveal() {
    var els = all(TARGETS).filter(function (el) {
      /* Never hide something that is already the whole visible page, and never
         hide a heading that a link may jump straight to. */
      return !el.closest(".hero") && !el.closest(".news-slider");
    });
    if (!els.length) return;

    /* Anything already on screen is marked done BEFORE anything is hidden.
       Without this, pressing play halfway down a page would hide what the
       reader is looking at for one frame and then fade it back in. */
    var vh = window.innerHeight || document.documentElement.clientHeight;
    els.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh && r.bottom > 0) {
        el.setAttribute("data-reveal", "done");
        el.classList.add("is-in");
      } else {
        el.setAttribute("data-reveal", "");
      }
    });
    els = els.filter(function (el) {
      return el.getAttribute("data-reveal") === "";
    });
    if (!els.length) return;

    if (!("IntersectionObserver" in window)) {
      revealEverything(); // failsafe (b)
      return;
    }

    observer = new IntersectionObserver(
      function (entries) {
        /* Group the entries arriving together and stagger them in document
           order, so a row of cards lands left to right rather than at random. */
        var arriving = entries.filter(function (e) {
          return e.isIntersecting;
        });
        arriving.sort(function (a, b) {
          var r = a.target.getBoundingClientRect();
          var s = b.target.getBoundingClientRect();
          return r.top - s.top || r.left - s.left;
        });
        arriving.forEach(function (entry, i) {
          var el = entry.target;
          el.style.setProperty("--reveal-i", Math.min(i, STAGGER_MAX));
          el.classList.add("is-in");
          el.setAttribute("data-reveal", "done");
          observer.unobserve(el);
        });
      },
      {
        /* -8% at the bottom: the block starts moving a little before it is
           fully on screen, which reads as anticipation rather than as a jump. */
        rootMargin: "0px 0px -8% 0px",
        threshold: 0.08
      }
    );

    els.forEach(function (el) {
      observer.observe(el);
    });

    window.setTimeout(revealEverything, FAILSAFE_MS); // failsafe (c)
  }

  /* ------------------------------------------------- hero drift + progress */

  function startScrollEffects() {
    if (onScroll) return; // already running; onChange can fire more than once
    var hero = document.querySelector(".hero-inner");
    var bar = document.querySelector(".scroll-progress");
    var nav = document.querySelector(".lab-nav");

    if (nav && !bar) {
      bar = document.createElement("div");
      bar.className = "scroll-progress";
      bar.setAttribute("aria-hidden", "true");
      nav.appendChild(bar);
    }
    if (!hero && !bar) return;

    function frame() {
      raf = 0;
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;

      if (hero) {
        var h = hero.offsetParent ? hero.offsetParent.offsetHeight : 0;
        if (h > 0 && y < h) {
          /* 0.18 of the scroll distance. Enough to read as depth against the
             video behind it, small enough that the text stays where the eye
             expects it. */
          hero.style.transform = "translate3d(0," + (y * 0.18).toFixed(1) + "px,0)";
          hero.style.opacity = Math.max(0, 1 - (y / h) * 1.15).toFixed(3);
        } else if (h > 0) {
          hero.style.opacity = "0";
        }
      }

      if (bar) {
        var doc = document.documentElement;
        var span = doc.scrollHeight - window.innerHeight;
        var p = span > 0 ? Math.min(1, Math.max(0, y / span)) : 0;
        bar.style.transform = "scaleX(" + p.toFixed(4) + ")";
      }
    }

    onScroll = function () {
      if (!raf) raf = window.requestAnimationFrame(frame);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    frame();
  }

  function stopScrollEffects() {
    if (onScroll) {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      onScroll = null;
    }
    if (raf) {
      window.cancelAnimationFrame(raf);
      raf = 0;
    }
    var hero = document.querySelector(".hero-inner");
    if (hero) {
      hero.style.transform = "";
      hero.style.opacity = "";
    }
    var bar = document.querySelector(".scroll-progress");
    if (bar) bar.style.transform = "scaleX(0)";
  }

  /* ------------------------------------------------------------------ boot */

  function boot() {
    /* Set BEFORE anything is hidden. body carries opacity:0 until window load,
       so nothing has painted yet and there is no flash. */
    document.documentElement.classList.add("js-reveal");

    window.LabMotion.onChange(function (running) {
      if (running) {
        if (!revealed) startReveal();
        startScrollEffects();
      } else {
        revealEverything();
        stopScrollEffects();
      }
    });
  }

  if (!window.LabMotion) return; // nothing to hook into; leave the page alone
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
