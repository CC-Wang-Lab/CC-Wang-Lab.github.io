/*
 * Partners strip — two rows, slow drift, arrows for manual control.
 *
 * WHY THIS IS NOT A CSS MARQUEE
 * The first version used @keyframes on a transform. That animates fine but it
 * cannot be scrubbed: the animation owns the transform, so an arrow button has
 * nothing to push. Driving `scrollLeft` instead gives manual control, and it
 * gives touch and trackpad swiping for free.
 *
 * THE SEAMLESS WRAP
 * Each row holds its list TWICE. When the scroll passes half the track, we
 * subtract exactly half. At that instant the second copy sits precisely where
 * the first began, so nothing appears to move. Any other distance shows a jump.
 *
 * Obeys the shared flag in motion.js, like everything else on the page.
 */
(function () {
  "use strict";

  var NUDGE = 380;   // px an arrow press adds
  var EASE = 0.12;   // how fast a nudge is consumed, per frame

  function init() {
    var root = document.getElementById("partners");
    if (!root) return;

    var scrollers = [].slice.call(root.querySelectorAll(".pt-scroller"));
    if (!scrollers.length) return;

    var rows = scrollers.map(function (el) {
      return {
        el: el,
        speed: parseFloat(el.getAttribute("data-speed")) || 30, // px per second
        pos: 0,
        nudge: 0,
        written: 0   // the last value THIS loop wrote, see the scroll handler

      };
    });

    // POSITION IS COMPUTED FROM ABSOLUTE TIME, not accumulated per frame.
    //
    // Measured in a background Chrome window: 12 animation frames fired over
    // 7590 ms of real time, but only 892 ms elapsed BETWEEN those frames -
    // Chrome delivers them in a burst and then sleeps. Anything that adds
    // `speed * dt` each frame therefore crawls whenever the window is not
    // focused. Deriving the position from elapsed wall-clock time instead is
    // correct however the frames arrive, and a long sleep simply resumes at the
    // right place. The wrap is seamless, so even a large jump is invisible.
    rows.forEach(function (r) {
      r.base = 0;                    // scroll position at the last resync
      r.baseTime = performance.now(); // when that was
    });

    function frame() {
      var now = performance.now();
      var moving = !window.LabMotion || window.LabMotion.isRunning();

      rows.forEach(function (r) {
        var h = r.el.scrollWidth / 2;   // one full copy of the list
        if (h <= 0) return;

        if (moving) {
          r.pos = r.base + r.speed * ((now - r.baseTime) / 1000);
        } else {
          // Paused: hold still, and keep the clock from running on underneath.
          r.base = r.pos;
          r.baseTime = now;
        }

        // Consume any arrow nudge, eased.
        if (r.nudge !== 0) {
          var step = r.nudge * EASE;
          if (Math.abs(step) < 0.5) step = r.nudge;
          r.base += step;
          r.pos += step;
          r.nudge -= step;
        }

        // Wrap both ways so the arrows can run backwards indefinitely.
        while (r.pos >= h) { r.pos -= h; r.base -= h; }
        while (r.pos < 0)  { r.pos += h; r.base += h; }

        r.written = Math.round(r.pos);
        r.el.scrollLeft = r.written;
      });

      if (window.__partners) window.__partners.frames++;
      requestAnimationFrame(frame);
    }

    function push(direction) {
      rows.forEach(function (r) {
        r.nudge += NUDGE * direction;
      });
    }

    var prev = root.querySelector(".pt-prev");
    var next = root.querySelector(".pt-next");
    if (prev) prev.addEventListener("click", function () { push(-1); });
    if (next) next.addEventListener("click", function () { push(1); });

    // A visitor who drags or swipes a row owns its position from then on;
    // pick the drift back up from wherever they left it.
    //
    // Compare against the value the loop last WROTE, never against `pos`.
    // The scroll event is asynchronous: by the time it arrives, `pos` has
    // already advanced another frame, so comparing with `pos` made every one of
    // our own writes look like a user drag and rolled the position back. That
    // turned 30 px/s into a measured 2 px/s.
    scrollers.forEach(function (el, i) {
      el.addEventListener("scroll", function () {
        if (Math.abs(el.scrollLeft - rows[i].written) > 2) {
          rows[i].pos = el.scrollLeft;
          rows[i].base = el.scrollLeft;
          rows[i].baseTime = performance.now();
        }
      }, { passive: true });
    });

    // Exposed so the drift can be measured without guessing at it.
    window.__partners = { rows: rows, frames: 0, lastDt: 0 };

    requestAnimationFrame(frame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
