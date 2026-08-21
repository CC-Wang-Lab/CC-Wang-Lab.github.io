/*
 * Media cards: the cursor spotlight and the tilt.
 *
 * Two effects, on .card-media, which is the research grid on the home page and
 * the project grid on /projects/. Both are POINTER effects. Neither one moves
 * anything on its own, which is why this file is short and why it does not
 * consult window.LabMotion.
 *
 *   SPOTLIGHT  a warm radial wash follows the cursor across the image
 *   TILT       the image leans up to 4 degrees toward the cursor
 *
 * This file writes four custom properties and nothing else. Every pixel of the
 * result is decided in _css/style.css:
 *
 *   --mx --my   cursor position over the image, in per cent
 *   --rx --ry   the tilt, in degrees
 *
 * WHY THIS IGNORES THE PAUSE BUTTON, AND WHY THAT IS NOT AN OVERSIGHT
 * .claude/rules/animation.md settles it: hover effects stay on under reduced
 * motion and under the pause button. They are user-initiated, they last a
 * quarter of a second, and switching them off leaves a site that feels broken
 * to the many Windows visitors who turn animation effects off for performance.
 * WCAG 2.2.2 governs motion that starts BY ITSELF. Nothing here does.
 *
 * The scroll-triggered half of this feature - the line drawings painting
 * themselves - is a different thing and does obey the pause button. It is pure
 * CSS riding the .is-in class that reveal.js already sets, so it is not in this
 * file at all. See the .card-art block in style.css.
 *
 * THREE THINGS HERE ARE NOT DECORATION
 *
 * 1. MOUSE ONLY. pointerType is checked on every entry. A tilt that fires on a
 *    finger tap leaves the card leaning after the finger has gone, because
 *    touch has no pointerleave in the way a mouse does. The CSS is additionally
 *    behind (hover: hover) and (pointer: fine), so this is belt and braces.
 *
 * 2. ITS OWN requestAnimationFrame TOKEN. reveal.js throttles the scroll
 *    handler with a token of its own. Sharing one would mean a scroll and a
 *    pointer move cancelling each other, which is the self-fighting handler
 *    this project has already paid for once.
 *
 * 3. pointermove IS BOUND ON ENTRY AND UNBOUND ON EXIT, per card, rather than
 *    delegated to the document. A delegated listener runs on every pixel of
 *    every mouse move anywhere on the page, to answer "no" almost always.
 *    will-change goes on and comes off with it: six cards each holding a
 *    promoted layer for the life of the page costs memory whether or not
 *    anybody ever hovers one.
 */
(function () {
  "use strict";

  /* Degrees. imec's vocabulary is small movements that read as depth rather
     than as an effect: the card lift is 1.25em and the image zoom is 2.5%.
     Four degrees belongs to that family. Eight does not. */
  var MAX_TILT = 4;

  var active = null; // the .card-media under the cursor, or null
  var frame = null;  // the .card-media-img inside it
  var px = 0;
  var py = 0;
  var raf = 0;       // this file's own token; see note 2 above

  function apply() {
    raf = 0;
    if (!active || !frame) return;

    var r = frame.getBoundingClientRect();
    if (!r.width || !r.height) return;

    /* 0..1 across the image box, then clamped: the cursor may legitimately be
       down over the title or the scope line, which sit outside this box. */
    var u = Math.min(1, Math.max(0, (px - r.left) / r.width));
    var v = Math.min(1, Math.max(0, (py - r.top) / r.height));

    active.style.setProperty("--mx", (u * 100).toFixed(2) + "%");
    active.style.setProperty("--my", (v * 100).toFixed(2) + "%");

    /* Move the mouse RIGHT and the card turns its right edge away, so rotateY
       takes +. Move it DOWN and the top edge comes toward you, so rotateX takes
       the negative. Getting that sign wrong is the difference between a card
       that follows the cursor and one that flinches from it. */
    active.style.setProperty("--ry", ((u - 0.5) * 2 * MAX_TILT).toFixed(2) + "deg");
    active.style.setProperty("--rx", ((0.5 - v) * 2 * MAX_TILT).toFixed(2) + "deg");
  }

  function onMove(e) {
    px = e.clientX;
    py = e.clientY;
    if (!raf) raf = window.requestAnimationFrame(apply);
  }

  function onEnter(e) {
    if (e.pointerType !== "mouse") return; // note 1
    var card = e.currentTarget;
    frame = card.querySelector(".card-media-img");
    if (!frame) return;
    active = card;
    card.classList.add("is-tracking");
    card.addEventListener("pointermove", onMove);
    onMove(e);
  }

  function onLeave(e) {
    var card = e.currentTarget;
    card.removeEventListener("pointermove", onMove);
    card.classList.remove("is-tracking");
    /* Clear rather than zero. An empty custom property falls back to the
       default in the var() call, which keeps the resting state in ONE place -
       the stylesheet - instead of half here and half there. */
    card.style.removeProperty("--rx");
    card.style.removeProperty("--ry");
    card.style.removeProperty("--mx");
    card.style.removeProperty("--my");
    if (card === active) {
      active = null;
      frame = null;
    }
    if (raf) {
      window.cancelAnimationFrame(raf);
      raf = 0;
    }
  }

  function boot() {
    /* Same belt-and-braces shape as reveal.js: the CSS that costs anything is
       behind a class only this script sets, so a script that never runs leaves
       a page that is merely plainer, never broken. */
    document.documentElement.classList.add("js-cards");

    var cards = document.querySelectorAll(".card-media");
    for (var i = 0; i < cards.length; i++) {
      cards[i].addEventListener("pointerenter", onEnter);
      cards[i].addEventListener("pointerleave", onLeave);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
