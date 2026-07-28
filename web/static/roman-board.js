/* The Roman target board's launch clock.
 *
 * Deliberately standalone: no Alpine component, no app.js entry. It reads one ISO timestamp off
 * the panel's data-launch attribute and writes four numbers, so it cannot be broken by — or
 * break — anything else on the site, and it has no registration-order relationship with Alpine.
 *
 * The build stamps the page, not the clock: a static page built in July and read in September
 * would otherwise show a stale countdown, so every value here is computed against the reader's
 * own clock at view time.
 *
 * After launch it counts UP rather than vanishing. The tech demo runs months after launch and
 * NASA publishes no per-target observation dates, so "T+ 34 days since launch" is the honest
 * thing to show — the board is waiting on observations, not on the rocket.
 */
(function () {
  "use strict";

  function start() {
    var panel = document.querySelector(".rtb-launch[data-launch]");
    if (!panel) return;
    var launch = Date.parse(panel.getAttribute("data-launch"));
    if (isNaN(launch)) return;

    var out = {};
    ["d", "h", "m", "s"].forEach(function (k) {
      out[k] = panel.querySelector('[data-rtb="' + k + '"]');
    });
    var when = panel.querySelector('[data-rtb="when"]');
    var whenText = when ? when.textContent : "";
    var labels = panel.querySelectorAll(".rtb-unit span");

    function pad(n) {
      return (n < 10 ? "0" : "") + n;
    }

    function tick() {
      var delta = launch - Date.now();
      var up = delta < 0;
      var secs = Math.floor(Math.abs(delta) / 1000);
      var d = Math.floor(secs / 86400);
      var h = Math.floor((secs % 86400) / 3600);
      var m = Math.floor((secs % 3600) / 60);
      var s = secs % 60;

      if (out.d) out.d.textContent = d.toLocaleString();
      if (out.h) out.h.textContent = pad(h);
      if (out.m) out.m.textContent = pad(m);
      if (out.s) out.s.textContent = pad(s);

      panel.classList.toggle("is-launched", up);
      if (when) when.textContent = up ? "Launched " + whenText : whenText;
      /* The first label carries the tense: "days" before, "days since" after. Screen readers
         and sighted readers get the same sentence either way. */
      if (labels.length) labels[0].textContent = up ? "days since" : "days";
    }

    tick();
    setInterval(tick, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
