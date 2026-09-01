/*
 * The one joke on this site.
 *
 * The hero caption reads "Onset of nucleate boiling in R1233zd...". Click that
 * sentence and the hero boils: bubbles nucleate along the bottom edge, grow as
 * they rise, wobble, and pop near the top.
 *
 * There is no reward text and no new string in ui.toml, on purpose. The
 * sentence you clicked IS the punchline, in both languages, and a caption that
 * explained the gag would stop it being one.
 *
 * WHY IT OBEYS THE MOTION FLAG
 * Nothing here starts on its own, so WCAG 2.2.2 does not reach it. It still
 * refuses to run while motion is paused, because on this site `motion-off`
 * means one thing only: the visitor pressed Pause on this page, a moment ago.
 * Nobody is locked out by that - motion starts running for everyone, and the
 * flag never survives a navigation. Pausing mid-boil clears the field at once.
 *
 * No markup was changed. The caption already exists on the home page and
 * nowhere else, which is also what scopes this script to the home page.
 */
(function () {
  "use strict";

  var caption = document.querySelector(".hero-caption");
  var hero = caption ? caption.closest(".hero") : null;
  if (!hero) return;

  // 34 sites over 2.4s of seeding. Enough to read as boiling, few enough that
  // a mashed caption cannot pile up hundreds of nodes: every click clears the
  // previous field before building the next one.
  var COUNT = 34;

  var field = null;
  var timer = null;

  function rand(lo, hi) {
    return lo + Math.random() * (hi - lo);
  }

  function stop() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (field && field.parentNode) {
      field.parentNode.removeChild(field);
    }
    field = null;
  }

  function boil() {
    if (window.LabMotion && !window.LabMotion.isRunning()) return;
    stop();

    // The rise distance is measured, not guessed: the hero is min(82vh, 720px)
    // and every visitor's is a different height.
    var rise = hero.offsetHeight + 60;
    var last = 0;

    field = document.createElement("div");
    field.className = "boil-field";
    field.setAttribute("aria-hidden", "true");

    for (var i = 0; i < COUNT; i++) {
      var life = rand(2.4, 4.2);
      var delay = rand(0, 2.4);
      var bubble = document.createElement("span");
      bubble.className = "boil-bubble";
      bubble.style.cssText =
        "--x:" + rand(2, 98).toFixed(2) + "%;" +
        "--d:" + rand(4, 15).toFixed(1) + "px;" +
        "--sway:" + rand(-14, 14).toFixed(1) + "px;" +
        "--rise:" + rise + "px;" +
        "--t:" + life.toFixed(2) + "s;" +
        "--delay:" + delay.toFixed(2) + "s;";
      field.appendChild(bubble);
      last = Math.max(last, life + delay);
    }

    hero.appendChild(field);
    // Take the nodes away once the last bubble has popped, so a home page left
    // open overnight is not carrying 34 finished elements.
    timer = setTimeout(stop, (last + 0.3) * 1000);
  }

  caption.addEventListener("click", boil);

  if (window.LabMotion) {
    window.LabMotion.onChange(function (running) {
      if (!running) stop();
    });
  }
})();
