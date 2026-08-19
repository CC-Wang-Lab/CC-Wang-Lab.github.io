/*
 * Projects — one grid, narrowed by a research-area chip.
 *
 * WHY A FILTER AND NOT A SECTION PER AREA
 * Sections put one card per row while the lab has fewer projects than areas, so
 * the page read as a column. See the note above hfun_project_grid in utils.jl.
 *
 * THE HASH IS THE CONTRACT
 * A research card on the home page links to /projects/#<area-id>. Nothing on
 * this page carries that id any more, so the browser will not scroll anywhere —
 * this script reads the hash instead and presses the matching chip. An unknown
 * hash falls back to "all" rather than showing an empty grid.
 *
 * history.replaceState, not pushState: filtering is not navigation, and pushing
 * a state per chip would make Back walk the filter bar instead of leaving the
 * page.
 */
(function () {
  "use strict";

  function init() {
    var bar = document.getElementById("projectFilter");
    var grid = document.getElementById("projectGrid");
    if (!bar || !grid) return;

    var chips = [].slice.call(bar.querySelectorAll(".pg-chip"));
    var items = [].slice.call(grid.querySelectorAll(".pg-item"));
    var scope = document.getElementById("projectScope");
    if (!chips.length || !items.length) return;

    function known(area) {
      for (var i = 0; i < chips.length; i++) {
        if (chips[i].getAttribute("data-area") === area) return true;
      }
      return false;
    }

    function apply(area, writeHash) {
      if (!known(area)) area = "all";

      chips.forEach(function (c) {
        var on = c.getAttribute("data-area") === area;
        c.classList.toggle("is-active", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
        if (on && scope) scope.textContent = c.getAttribute("data-scope") || "";
      });

      items.forEach(function (it) {
        it.hidden = !(area === "all" || it.getAttribute("data-area") === area);
      });

      if (writeHash && window.history && history.replaceState) {
        var url = location.pathname + location.search + (area === "all" ? "" : "#" + area);
        history.replaceState(null, "", url);
      }
    }

    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        apply(c.getAttribute("data-area"), true);
      });
    });

    // Arriving from a research card, or from a pasted link.
    window.addEventListener("hashchange", function () {
      apply(location.hash.replace(/^#/, ""), false);
    });

    apply(location.hash.replace(/^#/, ""), false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
