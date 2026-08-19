/*
 * Dark / light toggle.
 *
 * Two bugs from the source site are fixed here:
 *   1. There is no inline onclick="toggleDarkMode()". That function never
 *      existed, so every click threw a silent ReferenceError.
 *   2. The icon swap actually runs. On the source site it was commented out,
 *      so the sun and the moon were both visible at the same time.
 */
(function () {
  "use strict";

  var root = document.documentElement;

  function showIcon(theme) {
    var light = document.getElementById("iconLight");
    var dark = document.getElementById("iconDark");
    if (!light || !dark) return;
    // Show the icon for the theme you would switch TO.
    var isDark = theme === "dark";
    light.classList.toggle("d-none", !isDark);
    dark.classList.toggle("d-none", isDark);
  }

  function apply(theme) {
    root.setAttribute("data-bs-theme", theme);
    showIcon(theme);
    try {
      localStorage.setItem("labTheme", theme);
    } catch (e) {
      /* ignore — the theme still applies for this page view */
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    showIcon(root.getAttribute("data-bs-theme") || "light");

    var btn = document.getElementById("themeToggle");
    if (!btn) return;
    btn.addEventListener("click", function () {
      apply(root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark");
    });
  });

  // Follow the OS only while the visitor has not chosen for themselves.
  if (window.matchMedia) {
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", function (e) {
        var chosen = null;
        try {
          chosen = localStorage.getItem("labTheme");
        } catch (err) {
          /* ignore */
        }
        if (!chosen) {
          root.setAttribute("data-bs-theme", e.matches ? "dark" : "light");
          showIcon(e.matches ? "dark" : "light");
        }
      });
  }
})();
