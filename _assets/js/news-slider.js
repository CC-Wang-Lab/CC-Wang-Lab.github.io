/*
 * News carousel — a track of cards that moves.
 *
 * WHAT CHANGED, AND WHY IT IS NOT A STYLE PREFERENCE
 * This was a cross-fade: four slides stacked on top of each other, one visible,
 * a row of titles underneath. `.claude/rules/animation.md` recorded the imec
 * value it copied, "cross-fade, never a sideways slide", and that rule now
 * records this replacing it, asked for directly on 2026-09-01.
 *
 * The old shape also wasted the band. One item at a time filled the left half
 * of a 1425px panel and left the right half empty, and the left arrow sat
 * outside the rounded corner and was clipped by it. Two cards abreast fill it.
 *
 * HOW THE LOOP WORKS, AND WHY THERE ARE NO CLONES
 * Advancing slides the track one card to the left, and when the slide ends the
 * first card is MOVED TO THE END of the track and the transform is reset to
 * none. The picture does not change at that instant, so the reset is invisible,
 * and the carousel runs forever with exactly as many nodes as there are news
 * items. Going back does the same in reverse, off-screen, before animating.
 *
 * A cloned second copy would have been the other way. It doubles the DOM, and
 * every clone is a second article a screen reader has to be told to ignore.
 *
 * THE RESTING STATE IS ALWAYS A WHOLE CARD
 * That matters more here than it looks. `animation.md` requires every frame of
 * an animation to be a presentable still, because all sixteen audit shots are
 * taken with motion paused. Pausing stops the TIMER; it cannot stop a slide
 * half way, because between slides the track always sits at `transform: none`
 * with whole cards in the viewport.
 *
 * Auto-advance is governed by the shared flag in motion.js, never by
 * prefers-reduced-motion. The arrows work either way, paused or not.
 */
(function () {
  "use strict";

  var DWELL = 6000; // ms a card holds before the track moves on
  var SLIDE = 600;  // ms the move itself takes
  var EASE = "cubic-bezier(0.22, 0.61, 0.36, 1)";

  function init() {
    var root = document.getElementById("newsSlider");
    if (!root) return;

    var viewport = root.querySelector(".ns-viewport");
    var track = root.querySelector(".ns-track");
    var fill = root.querySelector(".ns-rail-fill");
    var prev = root.querySelector(".ns-prev");
    var next = root.querySelector(".ns-next");
    if (!viewport || !track || !track.firstElementChild) return;

    var dots = root.querySelectorAll(".ns-dot");
    var timer = null;
    var sliding = false;
    var held = false;
    var raf = 0;
    /* WHICH ITEM IS IN FRONT, counted in the order the build wrote them.
       The track reorders itself as it moves, so the DOM cannot answer this and
       the dots would have nothing to point at. */
    var index = 0;

    function running() {
      return window.LabMotion ? window.LabMotion.isRunning() : true;
    }

    /* Distance from one card's left edge to the next one's, gap included.
       Measured rather than computed, so the gap can change in the stylesheet
       at any breakpoint without a number to keep in step over here. */
    function stride() {
      var a = track.children[0];
      var b = track.children[1];
      if (!a) return 0;
      if (!b) return a.getBoundingClientRect().width;
      return b.getBoundingClientRect().left - a.getBoundingClientRect().left;
    }

    /* Nothing to scroll when every card is already on screen. Three items and
       three visible is a row, not a carousel, and a carousel that cannot move
       must not show controls promising that it can. */
    function fits() {
      var s = stride();
      if (!s) return true;
      return track.children.length <= Math.round(viewport.clientWidth / s);
    }

    function update() {
      raf = 0;
      root.classList.toggle("ns-static", fits());
    }

    function paintDots() {
      for (var i = 0; i < dots.length; i++) {
        var on = i === index;
        dots[i].classList.toggle("is-on", on);
        if (on) {
          dots[i].setAttribute("aria-current", "true");
        } else {
          dots[i].removeAttribute("aria-current");
        }
      }
    }

    function armRail() {
      if (!fill) return;
      fill.style.transition = "none";
      fill.style.transform = "translateX(-100%)";
      if (running() && !held && !document.hidden && !fits()) {
        void fill.offsetWidth; // force a reflow, or the two states collapse
        fill.style.transition = "transform " + DWELL + "ms linear";
        fill.style.transform = "translateX(0)";
      }
    }

    function stop() {
      window.clearTimeout(timer);
      timer = null;
    }

    function schedule() {
      stop();
      if (!running() || held || document.hidden || fits()) return;
      timer = window.setTimeout(function () {
        go(1);
      }, DWELL);
    }

    /* transitionend, with a timer behind it.
       Two reasons for the timer. A transition on a hidden or display:none
       element never fires one at all, and this element is inside a band a
       visitor can scroll past in a background tab. Without the failsafe
       `sliding` would stay true and the carousel would stop for good. */
    function settle(fn) {
      var done = false;
      function finish() {
        if (done) return;
        done = true;
        track.removeEventListener("transitionend", onEnd);
        window.clearTimeout(guard);
        fn();
      }
      /* The cards inside carry their own transforms for the hover lift and the
         tilt, and those events BUBBLE to the track. Without this test a mouse
         resting on a card would end the slide early, half way across. */
      function onEnd(e) {
        if (e.target === track && e.propertyName === "transform") finish();
      }
      var guard = window.setTimeout(finish, SLIDE + 150);
      track.addEventListener("transitionend", onEnd);
    }

    /* `steps` is how many cards to cross in ONE movement, which is what a dot
       needs: jumping from the first item to the third is one slide of two
       cards, not two slides. The timer and the arrows always pass 1. */
    function go(dir, steps) {
      if (sliding || fits()) return;
      var s = stride();
      if (!s) return;
      var n = track.children.length;
      steps = Math.max(1, Math.min(n - 1, steps || 1));
      var d = s * steps;
      var i;
      sliding = true;

      if (dir > 0) {
        track.style.transition = "transform " + SLIDE + "ms " + EASE;
        track.style.transform = "translate3d(" + -d + "px, 0, 0)";
        settle(function () {
          track.style.transition = "none";
          for (var k = 0; k < steps; k++) track.appendChild(track.firstElementChild);
          track.style.transform = "none";
          void track.offsetWidth;
          sliding = false;
        });
        index = (index + steps) % n;
      } else {
        // Put the cards in front first, off-screen, then walk back to them.
        track.style.transition = "none";
        for (i = 0; i < steps; i++) {
          track.insertBefore(track.lastElementChild, track.firstElementChild);
        }
        track.style.transform = "translate3d(" + -d + "px, 0, 0)";
        void track.offsetWidth;
        track.style.transition = "transform " + SLIDE + "ms " + EASE;
        track.style.transform = "none";
        settle(function () {
          track.style.transition = "none";
          sliding = false;
        });
        index = ((index - steps) % n + n) % n;
      }

      paintDots();
      armRail();
      schedule();
    }

    if (prev) prev.addEventListener("click", function () { go(-1, 1); });
    if (next) next.addEventListener("click", function () { go(1, 1); });

    for (var di = 0; di < dots.length; di++) {
      dots[di].addEventListener("click", function () {
        var n = track.children.length;
        var want = parseInt(this.getAttribute("data-goto"), 10);
        var ahead = ((want - index) % n + n) % n;
        if (!ahead) return;
        // Whichever way round is shorter. Six items, on the first, asked for
        // the last: go back one, not forward five.
        if (ahead * 2 > n) go(-1, n - ahead); else go(1, ahead);
      });
    }

    /* Hold still while somebody is TABBING through it.
       Pause-on-hover was in the cross-fade version and had to go: the band is
       wide, a pointer resting anywhere inside it stopped the timer, and the
       slider looked as though it never advanced at all. Keyboard focus is a
       deliberate act. A pointer passing over is not. */
    root.addEventListener("focusin", function () {
      held = true;
      armRail();
      stop();
    });
    root.addEventListener("focusout", function () {
      held = false;
      armRail();
      schedule();
    });

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        stop();
      } else {
        armRail();
        schedule();
      }
    });

    window.addEventListener("resize", function () {
      if (!raf) raf = window.requestAnimationFrame(function () {
        update();
        armRail();
        schedule();
      });
    });

    update();
    paintDots();
    if (window.LabMotion) {
      window.LabMotion.onChange(function () {
        armRail();
        schedule();
      });
    } else {
      armRail();
      schedule();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
