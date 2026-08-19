/*
 * News slider — the imec pattern.
 *
 * Slides cross-fade. The navigation underneath is a row of titles, each above a
 * progress line that fills across the slide's dwell time.
 *
 * Auto-advance is governed by the shared flag in motion.js, not by
 * prefers-reduced-motion directly. See the note at the top of that file for why.
 * The arrows and the title navigation always work, paused or not.
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
      ["ns-nav", "ns-prev", "ns-next"].forEach(function (c) {
        var el = root.querySelector("." + c);
        if (el) el.style.display = "none";
      });
      return;
    }

    var index = 0;
    var timer = null;
    var hovered = false;

    function running() {
      return window.LabMotion ? window.LabMotion.isRunning() : true;
    }

    function paint(next) {
      index = (next + slides.length) % slides.length;
      for (var i = 0; i < slides.length; i++) {
        slides[i].classList.toggle("is-active", i === index);
        navs[i].classList.toggle("is-active", i === index);
        navs[i].setAttribute("aria-current", i === index ? "true" : "false");

        var fill = navs[i].querySelector(".ns-nav-fill");
        fill.style.transition = "none";
        fill.style.transform = "translateX(-100%)";
        if (i === index && running() && !hovered) {
          void fill.offsetWidth; // force a reflow, or the two states collapse
          fill.style.transition = "transform " + DWELL + "ms linear";
          fill.style.transform = "translateX(0)";
        }
      }
    }

    function stop() {
      clearTimeout(timer);
      timer = null;
    }

    function schedule() {
      stop();
      if (!running() || hovered || document.hidden) return;
      timer = setTimeout(function () {
        paint(index + 1);
        schedule();
      }, DWELL);
    }

    function go(next) {
      paint(next);
      schedule();
    }

    root.querySelector(".ns-prev").addEventListener("click", function () { go(index - 1); });
    root.querySelector(".ns-next").addEventListener("click", function () { go(index + 1); });
    for (var i = 0; i < navs.length; i++) {
      navs[i].addEventListener("click", function () {
        go(parseInt(this.getAttribute("data-goto"), 10));
      });
    }

    // Hold still while somebody is reading or tabbing through it.
    function hold() { hovered = true; paint(index); stop(); }
    function release() { hovered = false; paint(index); schedule(); }
    root.addEventListener("mouseenter", hold);
    root.addEventListener("mouseleave", release);
    root.addEventListener("focusin", hold);
    root.addEventListener("focusout", release);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else { paint(index); schedule(); }
    });

    if (window.LabMotion) {
      window.LabMotion.onChange(function () { paint(index); schedule(); });
    } else {
      paint(0);
      schedule();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
