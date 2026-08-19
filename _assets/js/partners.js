/*
 * Partners strip — two independent bands drifting in opposite directions.
 *
 * WHY A TRANSFORM AND NOT scrollLeft
 * The first version animated `scrollLeft` and it visibly stepped. 26 px/s at
 * 60 fps is 0.43 px per frame, and a scroll offset is painted at whole device
 * pixels, so the strip stood still for two frames and then jumped one pixel.
 * Dropping the Math.round would not have helped: the rounding was in the
 * compositor, not in this file. A composited transform IS interpolated at
 * sub-pixel precision, so the drift is smooth at any speed.
 *
 * What that cost: native scrolling used to give touch and trackpad swiping for
 * free. The pointer-drag handler at the bottom of this file replaces it.
 *
 * THE SEAMLESS WRAP
 * Each track holds its list TWICE. When the offset passes one copy, exactly one
 * copy is subtracted. At that instant the second copy sits precisely where the
 * first began, so nothing appears to move. Any other distance shows a jump.
 *
 * DIRECTION
 * `data-speed` is px per second. Negative means the other way. Band 1 runs +26
 * and band 2 runs -26, and nothing else in here knows about direction.
 *
 * Obeys the shared flag in motion.js, like everything else on the page.
 */
(function () {
  "use strict";

  var NUDGE = 380;   // px an arrow press adds
  var EASE = 0.12;   // how much of a pending nudge is consumed per frame

  function init() {
    var root = document.getElementById("partners");
    if (!root) return;

    var bands = [].slice.call(root.querySelectorAll(".pt-band")).map(function (el) {
      var track = el.querySelector(".pt-track");
      if (!track) return null;
      return {
        el: el,
        track: track,
        speed: parseFloat(el.getAttribute("data-speed")) || 26,
        pos: 0,        // px scrolled from the start of the first copy
        base: 0,       // pos at the last resync
        baseTime: 0,   // when that resync was
        nudge: 0,
        dragging: false,
        dragX: 0
      };
    }).filter(Boolean);
    if (!bands.length) return;

    var now0 = performance.now();
    bands.forEach(function (b) { b.baseTime = now0; });

    // POSITION IS COMPUTED FROM ABSOLUTE TIME, not accumulated per frame.
    //
    // Measured in a background Chrome window: 12 animation frames fired over
    // 7590 ms of real time, but only 892 ms elapsed BETWEEN those frames -
    // Chrome delivers them in a burst and then sleeps. Anything that adds
    // `speed * dt` each frame therefore crawls whenever the window is not
    // focused. Deriving the position from elapsed wall-clock time instead is
    // correct however the frames arrive, and a long sleep simply resumes at the
    // right place. The wrap is seamless, so even a large jump is invisible.
    function frame() {
      var now = performance.now();
      var moving = !window.LabMotion || window.LabMotion.isRunning();

      bands.forEach(function (b) {
        var copy = b.track.scrollWidth / 2;   // one full copy of the list
        if (copy <= 0) return;

        if (moving && !b.dragging) {
          b.pos = b.base + b.speed * ((now - b.baseTime) / 1000);
        } else {
          // Paused or held: stand still, and keep the clock from running on.
          b.base = b.pos;
          b.baseTime = now;
        }

        // Consume any pending arrow nudge, eased.
        if (b.nudge !== 0) {
          var step = b.nudge * EASE;
          if (Math.abs(step) < 0.5) step = b.nudge;
          b.base += step;
          b.pos += step;
          b.nudge -= step;
        }

        // Wrap both ways, so the arrows can run backwards indefinitely.
        while (b.pos >= copy) { b.pos -= copy; b.base -= copy; }
        while (b.pos < 0)     { b.pos += copy; b.base += copy; }

        // Fractional on purpose. Rounding here is what made it step.
        b.track.style.transform = "translate3d(" + (-b.pos) + "px,0,0)";
      });

      if (window.__partners) window.__partners.frames++;
      requestAnimationFrame(frame);
    }

    // Arrows move ONLY their own band. Two rows sharing one pair of arrows was
    // the other half of what made the strip read as a single shaking block.
    bands.forEach(function (b) {
      var prev = b.el.querySelector(".pt-prev");
      var next = b.el.querySelector(".pt-next");
      if (prev) prev.addEventListener("click", function () { b.nudge -= NUDGE; });
      if (next) next.addEventListener("click", function () { b.nudge += NUDGE; });

      // Pointer drag, replacing the swipe that native scrolling gave for free.
      // Dragging holds the band still; releasing resumes the drift from wherever
      // it was left, which is the same contract the old scroll handler had.
      var view = b.el.querySelector(".pt-viewport");
      if (!view) return;

      view.addEventListener("pointerdown", function (e) {
        if (e.button !== 0 && e.pointerType === "mouse") return;
        b.dragging = true;
        b.dragX = e.clientX;
        b.nudge = 0;
        view.setPointerCapture(e.pointerId);
        view.classList.add("is-dragging");
      });

      view.addEventListener("pointermove", function (e) {
        if (!b.dragging) return;
        b.pos -= e.clientX - b.dragX;
        b.dragX = e.clientX;
        e.preventDefault();
      });

      function release(e) {
        if (!b.dragging) return;
        b.dragging = false;
        b.base = b.pos;
        b.baseTime = performance.now();
        try { view.releasePointerCapture(e.pointerId); } catch (err) { /* already gone */ }
        view.classList.remove("is-dragging");
      }
      view.addEventListener("pointerup", release);
      view.addEventListener("pointercancel", release);
    });

    // Exposed so the drift can be measured without guessing at it.
    window.__partners = { bands: bands, frames: 0 };

    requestAnimationFrame(frame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
