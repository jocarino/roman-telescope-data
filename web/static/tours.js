// Guided tour "story mode": the stops are all in the DOM, one is visible at a time. Alpine
// holds the index; this file also draws the active stop's planet — running the same wax/wane
// phase cycle as the planet page's hero, not a bare rotation — and wires arrow keys, swipes
// and #stop-N deep links. Page-scoped: only tour pages load it.

document.addEventListener("alpine:init", () => {
  Alpine.data("tour", (cfg) => ({
    n: (cfg && cfg.n) || 1,
    id: (cfg && cfg.id) || "",
    i: 0,
    // The intro box starts closed on every viewport. Nothing here is remembered between loads,
    // so opening by default meant it came back on every refresh however many times you shut it,
    // and three paragraphs pushed the first planet down the page each time. The ℹ beside the
    // kicker (in the accent colour) opens it for anyone who wants the framing.
    intro: false,

    // Analytics bookkeeping. Deliberately not part of the reactive state — nothing in the DOM
    // reads them, and Alpine would re-render the page on every stop for no reason.
    _seen: null,     // stop number -> true, for the stops this visit actually reached
    _done: false,    // has this visit already been counted as finishing the walk

    init() {
      this._seen = {};
      // Deep link: /tours/darkest-worlds#stop-4 opens on that stop (shareable mid-tour).
      const m = /^#stop-(\d+)$/.exec(location.hash || "");
      let entry = 1;
      if (m) {
        const k = parseInt(m[1], 10) - 1;
        if (k >= 0 && k < this.n) { this.i = k; entry = k + 1; }
      }
      // The pageview on /tours/<id> already says a tour was opened; this names WHICH tour
      // without a regex over the URL, and — with tour_stop_viewed and tour_completed below —
      // turns "does anyone finish one of these" into a funnel instead of a guess. `entry_stop`
      // above 1 is a shared #stop-N link: that visit never sees stop 1 and must not read as
      // someone who dropped out of the opening.
      this._track("tour_started", { entry_stop: entry });
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
    // Confirmation goes to the shared overlay toast, as everywhere else on the site.
    copy(hex) {
      navigator.clipboard?.writeText(hex);
      if (window.exoToast) window.exoToast("copied " + hex);
    },

    _sync(pushHash) {
      if (pushHash) history.replaceState(null, "", "#stop-" + (this.i + 1));
      this._reached(pushHash);
      this.$nextTick(() => window.TourStops && window.TourStops.draw(this.i));
    },

    // The progress curve: every stop this visit actually showed, once each. Not debounced,
    // unlike the phase slider — a tour is a dozen stops at most, so the count is bounded by
    // the tour's own length however hard someone leans on the arrow key, and dropping the
    // stops that flicked past would leave stops_seen below claiming stops with no event.
    //
    // `viaNav` is false for the first render, which is what keeps completion honest: reaching
    // the end is a move, so a #stop-N link that OPENS on the last stop is not a completion.
    // (A one-stop tour is the exception — arriving is the whole walk.) Once per page load, so
    // START AGAIN and a second lap stay one visit; a completion count above the start count
    // would read as a bug in the numbers rather than an enthusiastic visitor.
    _reached(viaNav) {
      const stop = this.i + 1;
      if (!this._seen[stop]) {
        this._seen[stop] = true;
        this._track("tour_stop_viewed", { stop: stop });
      }
      if ((viaNav || this.n === 1) && !this._done && this.i === this.n - 1) {
        this._done = true;
        this._track("tour_completed", { stops_seen: Object.keys(this._seen).length });
      }
    },

    // Every tour event carries which tour and how long it is, so "how far do people get"
    // is one query rather than a join against the tour list. No-op unless the build shipped
    // analytics — see web/static/analytics.js for the gate.
    _track(name, props) {
      if (!window.exoTrack) return;
      window.exoTrack(name, Object.assign({ tour_id: this.id, stops: this.n }, props));
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
// drawing needs no index fetch. The active stop runs PlanetRender.phaseCycle — literally the
// planet page's cycle, not a copy of it — so the terminator sweeps a full lunar cycle and the
// palette is retinted by the modelled colour at each phase: the planet lit, half-lit and
// crescent, never the black unlit disc.
(function () {
  "use strict";

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

  // `eff` is the illumination phase the cycle reports (0-170), not the raw geometry: the
  // readout has to name the picture on screen, and the picture never reaches 180.
  function readout(cv, eff) {
    var el = cv.parentNode && cv.parentNode.querySelector(".ts-phase b");
    if (!el) return;
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
      var idx0 = window.PlanetRender.phaseIndex(START_DEG, phases.length);
      window.PlanetRender.render(cv, Object.assign({}, o, {
        phase: (START_DEG * Math.PI) / 180,
        palette: tint(o.palette, phases, idx0),
      }));
      readout(cv, START_DEG);
      return;
    }

    // The cycle itself lives in PlanetRender so this and the planet page's hero cannot drift.
    var step = window.PlanetRender.phaseCycle(START_DEG, phases.length);
    window.PlanetRender.spin(cv, Object.assign({}, o, {
      frame: function (t) {
        var p = step(t);
        readout(cv, p.eff);
        // Per-frame overrides MUST be an object — spin() merges it over the base options.
        return { phase: p.rad, palette: tint(o.palette, phases, p.idx) };
      },
    }));
  }

  window.TourStops = { draw: draw };
})();
