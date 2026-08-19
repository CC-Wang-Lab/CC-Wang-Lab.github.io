/*
 * News slider — the imec pattern.
 *
 * Slides cross-fade. The navigation underneath is a row of titles, each above a
 * progress line that fills across the slide's dwell time.
 *
 * THE REDUCED-MOTION RULE
 * A visitor who has asked for reduced motion gets NO auto-advance and NO filling
 * progress bar. They still get the arrows and the title navigation, so nothing on
 * this page is unreachable. Note that on Windows "reduce motion" is just
 * Settings > Accessibility > Visual effects > Animation effects = Off, which is
 * common. Hiding content from those visitors is not acceptable.
 */
(function () {
  "use strict";

  var DWELL = 6000; // ms per slide

  function init() {
    var root = document.getElementById("newsSlider");
    if (!root) return;

    var slides = root.querySelectorAll(".ns-slide");
    var navs = root.querySelectorAll(".ns-nav-item");
    if (slides.length < 2) {
      root.querySelector(".ns-nav").style.display = "none";
      root.querySelector(".ns-prev").style.display = "none";
      root.querySelector(".ns-next").style.display = "none";
      return;
    }

    var reduce =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var index = 0;
    var timer = null;

    function paint(next) {
      index = (next + slides.length) % slides.length;
      for (var i = 0; i < slides.length; i++) {
        slides[i].classList.toggle("is-active", i === index);
        navs[i].classList.toggle("is-active", i === index);
        navs[i].setAttribute("aria-current", i === index ? "true" : "false");

        // Restart the fill animation only on the slide that just became active.
        var fill = navs[i].querySelector(".ns-nav-fill");
        fill.style.transition = "none";
        fill.style.transform = "translateX(-100%)";
        if (i === index && !reduce) {
          // force a reflow so the browser does not collapse the two states
          void fill.offsetWidth;
          fill.style.transition = "transform " + DWELL + "ms linear";
          fill.style.transform = "translateX(0)";
        }
      }
    }

    function schedule() {
      if (reduce) return;
      clearTimeout(timer);
      timer = setTimeout(function () {
        paint(index + 1);
        schedule();
      }, DWELL);
    }

    function go(next) {
      paint(next);
      schedule();
    }

    root.querySelector(".ns-prev").addEventListener("click", function () {
      go(index - 1);
    });
    root.querySelector(".ns-next").addEventListener("click", function () {
      go(index + 1);
    });
    for (var i = 0; i < navs.length; i++) {
      navs[i].addEventListener("click", function () {
        go(parseInt(this.getAttribute("data-goto"), 10));
      });
    }

    // Stop advancing while the visitor is reading or interacting.
    root.addEventListener("mouseenter", function () {
      clearTimeout(timer);
    });
    root.addEventListener("mouseleave", schedule);
    root.addEventListener("focusin", function () {
      clearTimeout(timer);
    });
    root.addEventListener("focusout", schedule);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) clearTimeout(timer);
      else schedule();
    });

    paint(0);
    schedule();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
