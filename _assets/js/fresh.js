/*
 * Nobody should ever have to press Ctrl+Shift+R on this site.
 *
 * THE PROBLEM, MEASURED
 * GitHub Pages sends `Cache-Control: max-age=600` on every HTML file and will
 * not let anyone change it. So for ten minutes after a deploy a visitor who
 * already has the page can be handed the OLD html out of their own browser
 * cache. `fingerprint()` in utils.jl already solved the other half of this by
 * hashing every CSS and JS url, so the old html can never wear a new
 * stylesheet. It cannot solve the html itself.
 *
 * WHAT THIS DOES
 * Every page carries `<meta name="lab-build">`, a hash of every source file the
 * site is built from. `build.txt` at the site root carries the same string.
 * This fetches that file with `cache: "no-store"`, and if the answer differs
 * from the meta in the page, the page it is sitting in is stale, so it reloads
 * once. The reload revalidates the document and the new html arrives.
 *
 * THE GUARD IS THE WHOLE DESIGN
 * A reload loop is the worst thing a website can do, so nothing here reloads
 * unless it can first prove it will remember having done so:
 *
 *   1. sessionStorage is TESTED, by writing and removing a key, before any
 *      other work. If it throws - private mode, blocked storage - this file
 *      returns and does nothing at all. It never reloads without a guard.
 *   2. The build id it saw is stored BEFORE the reload. One reload per build
 *      id per tab, for ever, even if the reload brings back the same stale
 *      page because the CDN edge has not caught up either.
 *   3. Any network failure is swallowed. Offline is not a reason to reload.
 *
 * WHY ONLY ON LOAD, AND NOT WHEN A TAB IS RE-FOCUSED
 * Reloading a page somebody is halfway through reading takes their place away.
 * Every navigation is a load, so a visitor who clicks anything gets the new
 * build. The only person who keeps an old page is one who sits on a single
 * page without clicking, and that is exactly the person not to interrupt.
 */
(function () {
  "use strict";

  var meta = document.querySelector('meta[name="lab-build"]');
  if (!meta) return;

  /* TRIMMED, and not because anything is untidy today.
     The minifier strips the quotes off this attribute, so the page ships
     `<meta name=lab-build  content=48f911e687f3  />`. An unquoted attribute
     value ends at the first space, so the browser hands back the bare hash and
     there is nothing to trim - which means this works by HTML's parsing rules
     rather than by anyone's intent. `build_id()` in utils.jl refuses to return
     anything but lowercase hex for the same reason. Both sides are trimmed so
     that neither of those has to stay true for this to keep working. */
  var mine = (meta.getAttribute("content") || "").trim();
  if (!mine) return;

  // Guard first. No storage, no reloading. See point 1 above.
  var store;
  try {
    store = window.sessionStorage;
    store.setItem("labFreshProbe", "1");
    store.removeItem("labFreshProbe");
  } catch (e) {
    return;
  }

  function check() {
    if (!window.fetch) return;
    // no-store defeats the browser's own cache; the query defeats anything
    // between here and the origin that ignores it.
    window.fetch("/build.txt?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (text) {
        if (!text) return;
        var live = text.trim();
        if (!live || live === mine) return;          // already the newest
        if (store.getItem("labFreshSeen") === live) return;  // tried once
        store.setItem("labFreshSeen", live);
        window.location.reload();
      })
      .catch(function () {
        /* offline, blocked, a 404 while the file is being deployed: leave the
           page exactly as it is. */
      });
  }

  if (document.readyState === "complete") {
    check();
  } else {
    window.addEventListener("load", check);
  }
})();
