// Guided tour "story mode": the stops are all in the DOM, one is visible at a time. Alpine
// holds the index; this file also draws the active stop's planet (the shared WebGL renderer,
// same as the gallery cards) and wires arrow keys, swipes and #stop-N deep links.
// Page-scoped — only tour pages load it.

document.addEventListener("alpine:init", () => {
  Alpine.data("tour", (cfg) => ({
    n: (cfg && cfg.n) || 1,
    i: 0,
    intro: false,

    init() {
      // Deep link: /tours/darkest-worlds#stop-4 opens on that stop (shareable mid-tour).
      const m = /^#stop-(\d+)$/.exec(location.hash || "");
      if (m) {
        const k = parseInt(m[1], 10) - 1;
        if (k >= 0 && k < this.n) this.i = k;
      }
      this.$watch("i", () => this._sync(true));
      this.$nextTick(() => this._sync(false));
      this._swipe();
    },

    go(k) {
      const next = Math.min(Math.max(k, 0), this.n - 1);
      if (next === this.i) return;
      this.i = next;
      // A stop is a screenful: land at the top of it rather than mid-panel.
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    next() { this.go(this.i + 1); },
    prev() { this.go(this.i - 1); },
    pad(k) { return String(k).padStart(2, "0"); },

    // The palette block is the site's shared one, which calls copy() on a swatch click.
    msg: "",
    copy(hex) {
      navigator.clipboard?.writeText(hex);
      this.msg = "copied " + hex;
      clearTimeout(this._flash);
      this._flash = setTimeout(() => (this.msg = ""), 1600);
    },

    _sync(pushHash) {
      if (pushHash) history.replaceState(null, "", "#stop-" + (this.i + 1));
      this.$nextTick(() => window.TourStops && window.TourStops.draw(this.i));
    },

    // Sideways swipe steps the tour on touch devices; vertical drags stay scrolls.
    _swipe() {
      let x0 = null, y0 = null;
      const el = this.$el;
      el.addEventListener("pointerdown", (e) => {
        if (e.pointerType === "mouse") return;
        x0 = e.clientX; y0 = e.clientY;
      }, { passive: true });
      el.addEventListener("pointerup", (e) => {
        if (x0 === null) return;
        const dx = e.clientX - x0, dy = e.clientY - y0;
        x0 = null;
        if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.6) {
          if (dx < 0) this.next(); else this.prev();
        }
      }, { passive: true });
    },
  }));
});

// ── Planet renders ──────────────────────────────────────────────────────────
// Each stop's canvas carries its own palette/radius/cloud/brightness, so drawing needs no
// index fetch. Drawn on first view and cached; hovering spins the sphere, as in the gallery.
(function () {
  "use strict";

  function optsFor(cv) {
    var pal = (cv.dataset.palette || "").split(",").filter(Boolean);
    if (!pal.length) return null;
    return {
      palette: pal,
      radius: parseFloat(cv.dataset.radius) || null,
      cloudState: cv.dataset.cloud || "",
      lumY: parseFloat(cv.dataset.lum) || 0,
      style: localStorage.getItem("planetStyle") || "retro",
      fidelity: localStorage.getItem("renderFidelity") || "classic",
      phase: window.PlanetRender ? window.PlanetRender.hashPhase(cv.dataset.pid || "") : 0,
    };
  }

  function draw(index) {
    var sections = document.querySelectorAll(".tour-stop");
    var cv = sections[index] && sections[index].querySelector(".ts-planet");
    if (!cv || !window.PlanetRender || cv.dataset.drawn === "1") return;
    var o = optsFor(cv);
    if (!o) return;
    window.PlanetRender.render(cv, o);
    cv.dataset.drawn = "1";
  }

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hoverable = window.matchMedia && window.matchMedia("(hover: hover)").matches;

  function spinner(start) {
    var t0 = null;
    return function (t) {
      if (t0 === null) t0 = t;
      return start + ((t - t0) / 1000) * 0.45;  // ~14 s per turn: a drift, not a spin
    };
  }

  if (hoverable && !reduced) {
    document.addEventListener("mouseover", function (e) {
      var cv = e.target.closest && e.target.closest(".ts-planet");
      if (!cv || !window.PlanetRender) return;
      var o = optsFor(cv);
      if (o) window.PlanetRender.spin(cv, Object.assign({}, o, { frame: spinner(o.phase) }));
    });
    document.addEventListener("mouseout", function (e) {
      var cv = e.target.closest && e.target.closest(".ts-planet");
      if (!cv || !window.PlanetRender) return;
      window.PlanetRender.stop(cv);
      var o = optsFor(cv);
      if (o) window.PlanetRender.render(cv, o);
    });
  }

  window.TourStops = { draw: draw };
})();
