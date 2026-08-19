/*
 * One motion flag for the whole page.
 *
 * The hero video, the news slider and the partners strip all move by themselves.
 * Three separate pause buttons would be three things to find; one control that
 * stops all of them is easier to use and easier to reason about.
 *
 * WHY THIS OVERRIDES prefers-reduced-motion
 * The earlier version obeyed that preference and refused to start anything. On
 * Windows the preference is set by Settings > Accessibility > Visual effects >
 * Animation effects = Off, which a lot of people switch off for performance
 * rather than for motion sensitivity. Those visitors got a frozen page with no
 * way to start it, and no idea why.
 *
 * What replaces it is the requirement that actually applies, WCAG 2.2.2
 * "Pause, Stop, Hide": motion that starts on its own and runs past five seconds
 * must have a mechanism to stop it. That mechanism is this control. It is
 * visible, it is keyboard reachable, and the choice is remembered.
 *
 * Everything starts running, for everyone. The control is what makes that
 * acceptable, and the reasoning is spelled out again at the `running` default
 * below so nobody re-introduces the old behaviour by accident.
 */
window.LabMotion = (function () {
  "use strict";

  var KEY = "labMotion"; // "on" | "off"
  var listeners = [];

  function stored() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  // MOTION STARTS RUNNING FOR EVERYONE.
  //
  // prefers-reduced-motion is deliberately NOT consulted here. It was, in two
  // earlier versions, and both times the result was a frozen page for a large
  // share of Windows visitors who had switched animation effects off for
  // performance and had no idea that was why the video would not play.
  //
  // The requirement that actually applies is WCAG 2.2.2 "Pause, Stop, Hide":
  // motion that starts on its own and runs past five seconds needs a mechanism
  // to stop it. That mechanism is the visible, keyboard-reachable control this
  // file drives, and the choice is remembered across pages and visits.
  //
  // An explicit choice always wins over the default.
  var running = stored() ? stored() === "on" : true;

  function apply() {
    document.documentElement.classList.toggle("motion-off", !running);
    for (var i = 0; i < listeners.length; i++) {
      try {
        listeners[i](running);
      } catch (e) {
        /* one broken listener must not stop the others */
      }
    }
    var btns = document.querySelectorAll("[data-motion-toggle]");
    for (var j = 0; j < btns.length; j++) {
      btns[j].setAttribute("aria-pressed", running ? "false" : "true");
      btns[j].classList.toggle("is-paused", !running);
    }
  }

  return {
    /** Is motion currently running? */
    isRunning: function () {
      return running;
    },
    /** Call fn(running) now and on every change. */
    onChange: function (fn) {
      listeners.push(fn);
      fn(running);
    },
    set: function (value) {
      running = !!value;
      try {
        localStorage.setItem(KEY, running ? "on" : "off");
      } catch (e) {
        /* the choice still holds for this page view */
      }
      apply();
    },
    toggle: function () {
      this.set(!running);
    },
    init: function () {
      var btns = document.querySelectorAll("[data-motion-toggle]");
      for (var i = 0; i < btns.length; i++) {
        btns[i].addEventListener("click", function () {
          window.LabMotion.toggle();
        });
      }
      apply();
    },
  };
})();

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () {
    window.LabMotion.init();
  });
} else {
  window.LabMotion.init();
}
