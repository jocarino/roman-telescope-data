// Guided tour "story mode": the stops are all in the DOM, one is visible at a time. Alpine
// holds the index; this file also draws the active stop's planet — running the same wax/wane
// phase cycle as the planet page's hero, not a bare rotation — and wires arrow keys, swipes
// and #stop-N deep links. Page-scoped: only tour pages load it.

document.addEventListener("alpine:init", () => {
  Alpine.data("tour", (cfg) => ({
    n: (cfg && cfg.n) || 1,
    i: 0,
    // The intro box opens by default so anyone arriving cold gets the point of the tour — but
    // not on a phone, where three paragraphs would push the first planet off the screen
    // entirely. There the ℹ (in the accent colour, right beside the kicker) opens it.
    intro: !(window.matchMedia && window.matchMedia("(max-width: 760px)").matches),

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
      // Deliberately no scrolling: stops are the same shape, so staying put keeps whatever
      // you were reading — caption, facts, palette — under your eyes as the planet changes.
      this.i = next;
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

    // Sideways swipe steps the tour on touch devices. Touch events rather than pointer
    // events: a vertical scroll fires pointercancel and the pointerup never arrives, so a
    // pointer-based swipe silently stops working the moment the page can scroll.
    _swipe() {
      let x0 = null, y0 = null;
      const el = this.$el;
      el.addEventListener("touchstart", (e) => {
        if (e.touches.length !== 1) { x0 = null; return; }
        x0 = e.touches[0].clientX; y0 = e.touches[0].clientY;
      }, { passive: true });
      el.addEventListener("touchend", (e) => {
        if (x0 === null || !e.changedTouches.length) return;
        const dx = e.changedTouches[0].clientX - x0;
        const dy = e.changedTouches[0].clientY - y0;
        x0 = null;
        if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.2) {
          if (dx < 0) this.next(); else this.prev();
        }
      }, { passive: true });
    },
  }));
});

// ── Planet renders ──────────────────────────────────────────────────────────
// Each stop's canvas carries its own palette, attributes and phase-resolved colours, so
// drawing needs no index fetch. The active stop runs the phase cycle from the planet page:
// the terminator sweeps a full lunar cycle and the palette is retinted by the modelled
// colour at each phase, so you see the planet lit, half-lit and backlit — not a spinning ball.
(function () {
  "use strict";

  var PHASE_SPEED = 16;   // degrees per second, matching the planet page's hero
  var START_DEG = 20;     // the page's default phase: enough terminator to read as 3D
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
    };
  }

  function phasesOf(cv) {
    try { return JSON.parse(cv.dataset.phases || "[]"); } catch (e) { return []; }
  }

  function rgb(hex) { return [1, 3, 5].map(function (i) { return parseInt(hex.slice(i, i + 2), 16); }); }

  // Retint a palette by the per-channel drift of the phase colour against full phase, so the
  // render carries the modelled colour shift as the planet wanes. (Same maths as app.js.)
  function tint(palette, phases, idx) {
    var ph = phases[idx];
    if (!ph || !ph.d || !phases.length) return palette;
    var base = rgb(phases[0].h), cur = rgb(ph.h);
    var ratio = cur.map(function (v, i) { return v / (base[i] || 1); });
    return palette.map(function (hex) {
      return "#" + rgb(hex).map(function (v, i) {
        var c = Math.max(0, Math.min(255, Math.round(v * ratio[i])));
        return c.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function phaseName(d) {
    if (d < 5) return "FULLY LIT";
    if (d < 90) return "GIBBOUS";
    if (d < 95) return "HALF LIT";
    if (d < 175) return "CRESCENT";
    return "BACKLIT";
  }

  function readout(cv, deg) {
    var el = cv.parentNode && cv.parentNode.querySelector(".ts-phase b");
    if (!el) return;
    var eff = deg <= 180 ? deg : 360 - deg;
    var txt = Math.round(eff) + "° · " + phaseName(eff);
    if (el.textContent !== txt) el.textContent = txt;
  }

  function draw(index) {
    if (!window.PlanetRender) return;
    var sections = document.querySelectorAll(".tour-stop");
    for (var k = 0; k < sections.length; k++) {
      var c = sections[k].querySelector(".ts-planet");
      if (c && k !== index) window.PlanetRender.stop(c);
    }
    var cv = sections[index] && sections[index].querySelector(".ts-planet");
    if (!cv) return;
    var o = optsFor(cv);
    if (!o) return;
    var phases = phasesOf(cv);

    if (reduced || phases.length < 2) {
      // No cycle: hold the default phase, still lit like the planet page rather than flat.
      var idx0 = Math.round(START_DEG / 10);
      window.PlanetRender.render(cv, Object.assign({}, o, {
        phase: (START_DEG * Math.PI) / 180,
        palette: tint(o.palette, phases, idx0),
      }));
      readout(cv, START_DEG);
      return;
    }

    var anim = { deg: START_DEG, last: null };
    window.PlanetRender.spin(cv, Object.assign({}, o, {
      frame: function (t) {
        if (anim.last === null) anim.last = t;
        anim.deg += PHASE_SPEED * (Math.min(t - anim.last, 100) / 1000);
        anim.last = t;
        if (anim.deg >= 360) anim.deg -= 360;
        var eff = anim.deg <= 180 ? anim.deg : 360 - anim.deg;
        var idx = Math.max(0, Math.min(phases.length - 1, Math.round(eff / 10)));
        readout(cv, anim.deg);
        // Per-frame overrides MUST be an object — spin() merges it over the base options.
        return {
          phase: (anim.deg * Math.PI) / 180,
          palette: tint(o.palette, phases, idx),
        };
      },
    }));
  }

  window.TourStops = { draw: draw };
})();
