/*
 * The inquiry form on /contact/.
 *
 * TWO MODES, ONE FORM
 * GitHub Pages has no server, so this form either posts to a third party or it
 * builds a mailto: link. `form_endpoint` in config.md decides, and the markup
 * carries the answer in data-live.
 *
 *   data-live="1"   POST to the endpoint with fetch, stay on the page, and say
 *                   what happened in the status line.
 *   data-live="0"   Build a mailto: URL from the answers and hand it to the
 *                   visitor's mail program. Nothing is sent by us; they press
 *                   send. It needs no account anywhere, which is why it is the
 *                   default rather than a dead button.
 *
 * A plain <form action="mailto:..."> is NOT used for the second mode. Browsers
 * disagree about it, several post the fields as an unreadable attachment, and
 * Chrome shows a scary "this will send unencrypted" dialog. Composing the URL
 * ourselves produces a readable email every time.
 */
(function () {
  "use strict";

  function init() {
    var form = document.getElementById("inquiryForm");
    if (!form) return;

    var status = form.querySelector(".ff-status");
    var button = form.querySelector('button[type="submit"]');
    var live = form.getAttribute("data-live") === "1";

    function say(kind) {
      if (!status) return;
      status.textContent = status.getAttribute("data-" + kind) || "";
      status.className = "ff-status is-" + kind;
    }

    // Label text, without the "Required" chip, so the email reads like prose.
    function labelOf(field) {
      var el = form.querySelector('label[for="' + field.name + '"]');
      if (!el) return field.name;
      var clone = el.cloneNode(true);
      var chip = clone.querySelector(".ff-req");
      if (chip) chip.remove();
      return clone.textContent.trim().replace(/\s+/g, " ");
    }

    function fields() {
      return [].slice.call(form.elements).filter(function (el) {
        return el.name && el.name.charAt(0) !== "_" &&
               el.name !== "access_key" && el.name !== "botcheck" &&
               el.name !== "subject" && el.name !== "from_name" &&
               el.type !== "submit";
      });
    }

    form.addEventListener("submit", function (e) {
      // The honeypot. A person never sees it, so anything in it is a bot.
      //
      // The NAME is not fixed: Formspree wants _gotcha (a text input) and
      // Web3Forms wants botcheck (a checkbox). utils.jl emits whichever the
      // configured endpoint needs and tells us which in data-trap, so this
      // check cannot drift out of step with the markup.
      var trapName = form.getAttribute("data-trap") || "_gotcha";
      var trap = form.querySelector('[name="' + trapName + '"]');
      if (trap && (trap.type === "checkbox" ? trap.checked : trap.value)) {
        e.preventDefault();
        return;
      }

      if (!live) {
        e.preventDefault();
        var to = form.getAttribute("data-mailto") || "";
        var lines = fields().map(function (el) {
          return labelOf(el) + "\n" + (el.value || "-") + "\n";
        });
        var url = "mailto:" + to +
          "?subject=" + encodeURIComponent("Project inquiry - CC Wang Lab") +
          "&body=" + encodeURIComponent(lines.join("\n"));
        window.location.href = url;
        return;
      }

      e.preventDefault();
      say("sending");
      if (button) button.disabled = true;

      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" }
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        say("sent");
      }).catch(function () {
        say("failed");
      }).then(function () {
        if (button) button.disabled = false;
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
