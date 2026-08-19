/*
 * Hero video control.
 *
 * The markup has NO `autoplay` attribute. That is deliberate: with it present
 * the browser restarts the video after a script pauses it, so the visitor's
 * reduced-motion preference could not be honoured. Starting is decided here.
 *
 * Two cases leave the video paused, and BOTH show a play button rather than a
 * dead still image:
 *   1. The visitor asked for reduced motion. On Windows that is just
 *      Settings > Accessibility > Visual effects > Animation effects = Off,
 *      which many people switch off for performance. It is not rare.
 *   2. The browser blocked playback by policy.
 */
(function () {
  "use strict";

  function start() {
    var video = document.querySelector(".hero-video");
    var button = document.getElementById("heroPlay");
    if (!video || !button) return;

    function offerPlay() {
      button.classList.add("is-shown");
    }

    button.addEventListener("click", function () {
      video.play();
      button.classList.remove("is-shown");
    });

    var reduce =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduce) {
      offerPlay();
      return;
    }

    var attempt = video.play();
    if (attempt && typeof attempt.catch === "function") {
      attempt.catch(offerPlay);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
