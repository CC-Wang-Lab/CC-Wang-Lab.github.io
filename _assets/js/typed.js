/*
 * The typed line under the hero headline.
 *
 * Types a phrase, holds it, deletes it, types the next, forever.
 *
 * Two things this does that a naive version does not:
 *
 * 1. The first phrase is already in the HTML. So a screen reader, a search
 *    engine, and a visitor with JavaScript off all see a real sentence. The
 *    script only takes over once it runs.
 * 2. The line reserves the width of the LONGEST phrase up front, in a hidden
 *    sizing span. Without that the layout shifts on every character and the
 *    buttons underneath jump around.
 *
 * Governed by the shared flag in motion.js: paused means the current phrase
 * stays on screen, complete. It never leaves a half-typed word.
 */
(function () {
  "use strict";

  var TYPE = 55;    // ms per character typed
  var ERASE = 28;   // ms per character deleted
  var HOLD = 1900;  // ms a complete phrase stays
  var GAP = 420;    // ms of blank before the next phrase

  function init() {
    var el = document.getElementById("typedLine");
    if (!el) return;

    var phrases;
    try {
      phrases = JSON.parse(el.getAttribute("data-phrases") || "[]");
    } catch (e) {
      return;
    }
    if (!phrases.length) return;

    var out = el.querySelector(".typed-text");
    if (!out) return;

    var i = 0, ch = 0, deleting = false, timer = null, paused = false;

    function step() {
      if (paused) return;
      var phrase = phrases[i];

      if (!deleting) {
        ch++;
        out.textContent = phrase.slice(0, ch);
        if (ch >= phrase.length) {
          deleting = true;
          timer = setTimeout(step, HOLD);
          return;
        }
        timer = setTimeout(step, TYPE);
      } else {
        ch--;
        out.textContent = phrase.slice(0, ch);
        if (ch <= 0) {
          deleting = false;
          i = (i + 1) % phrases.length;
          timer = setTimeout(step, GAP);
          return;
        }
        timer = setTimeout(step, ERASE);
      }
    }

    function run() {
      paused = false;
      clearTimeout(timer);
      timer = setTimeout(step, 900); // let the page settle before it starts
    }

    function halt() {
      paused = true;
      clearTimeout(timer);
      // Leave a whole phrase on screen, never a fragment.
      out.textContent = phrases[i];
      ch = phrases[i].length;
      deleting = false;
    }

    if (window.LabMotion) {
      window.LabMotion.onChange(function (running) {
        if (running) run();
        else halt();
      });
    } else {
      run();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
