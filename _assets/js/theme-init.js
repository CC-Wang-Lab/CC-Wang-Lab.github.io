/*
 * Runs in <head>, before the first paint, so the page never flashes the wrong
 * colour. Nothing else here may touch the theme before this has run.
 *
 * Fixed from the source site: it hardcoded "dark" and ignored the operating
 * system setting. A visitor whose laptop is in light mode got a dark page.
 */
(function () {
  var saved = null;
  try {
    saved = localStorage.getItem("labTheme");
  } catch (e) {
    /* private browsing can throw on localStorage; fall through to the OS */
  }
  var prefersDark =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var theme = saved || (prefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-bs-theme", theme);
})();
