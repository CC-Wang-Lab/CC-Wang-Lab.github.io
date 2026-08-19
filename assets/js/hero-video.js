/*
 * Hero video.
 *
 * The markup has NO `autoplay` attribute. That is deliberate: with it present
 * the browser restarts the video after a script pauses it, so the pause control
 * could not hold. Starting and stopping is decided here, from the shared flag
 * in motion.js.
 *
 * It loops forever (`loop` in the markup) and it is muted, which is not
 * optional: Chrome and Safari refuse to autoplay a video with an audio track,
 * and they fail silently.
 */
(function () {
  "use strict";

  function start() {
    var video = document.querySelector(".hero-video");
    if (!video || !window.LabMotion) return;

    function play() {
      var attempt = video.play();
      if (attempt && typeof attempt.catch === "function") {
        // Autoplay can still be blocked by browser policy. If it is, flip the
        // shared flag so the pause control shows "play" and one click fixes it.
        attempt.catch(function () {
          window.LabMotion.set(false);
        });
      }
    }

    window.LabMotion.onChange(function (running) {
      if (running) play();
      else video.pause();
    });

    // Some browsers drop playback when the tab is hidden and do not resume.
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && window.LabMotion.isRunning() && video.paused) play();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
