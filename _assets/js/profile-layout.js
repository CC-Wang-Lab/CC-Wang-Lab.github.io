/* Temporary, shareable profile-layout comparison. No choice is persisted. */
(function () {
  "use strict";

  var allowed = ["editorial", "dossier", "narrative"];
  var root = document.documentElement;

  function selectedFromUrl() {
    var value = new URL(window.location.href).searchParams.get("profile-layout");
    return allowed.indexOf(value) === -1 ? null : value;
  }

  function syncLanguageLink(value) {
    var link = document.querySelector(".lang-switch");
    if (!link) return;
    var url = new URL(link.getAttribute("href"), window.location.href);
    if (value) url.searchParams.set("profile-layout", value);
    else url.searchParams.delete("profile-layout");
    link.setAttribute("href", url.pathname + url.search + url.hash);
  }

  function render(value) {
    var switcher = document.querySelector("[data-profile-switcher]");
    var active = value || "editorial";
    root.setAttribute("data-profile-layout", active);
    root.setAttribute("data-profile-layout-compare", value ? "true" : "false");
    syncLanguageLink(value);
    if (!switcher) return;

    switcher.hidden = false;
    switcher.querySelectorAll("[data-profile-layout-choice]").forEach(function (choice) {
      choice.setAttribute(
        "aria-pressed",
        choice.getAttribute("data-profile-layout-choice") === active ? "true" : "false"
      );
    });
  }

  function choose(value) {
    if (allowed.indexOf(value) === -1) return;
    var url = new URL(window.location.href);
    url.searchParams.set("profile-layout", value);
    history.replaceState(null, "", url.pathname + url.search + url.hash);
    render(value);
  }

  function init() {
    var switcher = document.querySelector("[data-profile-switcher]");
    if (!switcher) return;
    render(selectedFromUrl());
    switcher.addEventListener("click", function (event) {
      var choice = event.target.closest("[data-profile-layout-choice]");
      if (!choice || !switcher.contains(choice)) return;
      choose(choice.getAttribute("data-profile-layout-choice"));
    });
    window.addEventListener("popstate", function () {
      render(selectedFromUrl());
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
