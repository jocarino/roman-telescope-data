/* Model space: the migration slider, the colour year, and the what-if knobs.
 *
 * Deliberately a separate Alpine component from `detail` in app.js, with its own swatch and
 * its own canvas, rather than driving the page's hero. Two reasons: the panels then read as a
 * side-by-side "what if" against the real colour that stays on screen above them — which is
 * the honest framing, since none of this is the planet — and app.js is left untouched, which
 * is what keeps parallel sessions on this repo from colliding (see CLAUDE.md).
 *
 * Every colour shown here is precomputed in Python (web/modelspace.py); this file only picks
 * between stops and interpolates between neighbours. It never does colour science of its own.
 */
(function () {
  "use strict";

  function hexToRgb(h) {
    var s = String(h || "").replace("#", "");
    if (s.length !== 6) return [0, 0, 0];
    return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
  }

  function two(n) {
    var s = Math.max(0, Math.min(255, Math.round(n))).toString(16);
    return s.length < 2 ? "0" + s : s;
  }

  /* Blend two track stops. Only ever used BETWEEN adjacent precomputed stops, which sit a
   * fraction of an octave apart, so a plain sRGB mix cannot wander anywhere the physics did
   * not already go — it just stops the swatch from stepping visibly as the slider moves. */
  function mixHex(a, b, t) {
    var x = hexToRgb(a), y = hexToRgb(b);
    return "#" + two(x[0] + (y[0] - x[0]) * t) + two(x[1] + (y[1] - x[1]) * t) +
      two(x[2] + (y[2] - x[2]) * t);
  }

  /* Distances span nine orders of magnitude across the archive; one format does not fit. */
  function fmtAu(au) {
    if (au == null) return "—";
    if (au < 0.01) return au.toFixed(4).replace(/0+$/, "").replace(/\.$/, "") + " AU";
    if (au < 1) return au.toFixed(3) + " AU";
    if (au < 100) return au.toFixed(2) + " AU";
    return Math.round(au).toLocaleString() + " AU";
  }

  function fmtTemp(k) {
    return Math.round(k).toLocaleString() + " K";
  }

  /* Plain-English regime name for a temperature. The slider's whole point is that the planet
   * crosses these, so naming them is what turns a moving swatch into an explanation. */
  function regime(k) {
    if (k >= 1600) return "ultra-hot — cloud-free, very dark";
    if (k >= 900) return "hot — clouds gone, sodium eats the yellow";
    if (k >= 500) return "warm — methane breaking up, hazy";
    if (k >= 220) return "temperate — water and ammonia clouds";
    return "cold — thick cloud, methane frozen in";
  }

  /* Each what-if variant's wording is identical on every planet page, so it is shipped once
   * here rather than inlined 5,800 times. Keys must match the ids in pipeline/modelspace.py. */
  var WHATIF_TEXT = {
    "clouds-off": {
      label: "No clouds at all",
      detail: "Strip the cloud deck and you see straight down into the deep atmosphere: much " +
        "darker, and bluer where Rayleigh scattering takes over.",
    },
    "clouds-thick": {
      label: "Solid cloud deck",
      detail: "Close the cloud deck completely. Clouds are bright and fairly grey, so this " +
        "pushes almost any planet toward a pale version of its star's own colour.",
    },
    "metal-poor": {
      label: "Solar metallicity (1×)",
      detail: "As few heavy elements as the Sun. Less methane to absorb the red end, so the " +
        "colour drifts back toward the star's.",
    },
    "metal-rich": {
      label: "Metal-rich (30×)",
      detail: "Thirty times the Sun's heavy elements — Neptune territory. Deeper methane " +
        "bands eat the red and the planet swings blue-green.",
    },
  };

  function textFor(id) {
    return WHATIF_TEXT[id] || { label: id, detail: "" };
  }

  document.addEventListener("alpine:init", function () {
    Alpine.data("modelspace", function (init) {
      return {
        // Parallel arrays: {r, au, t, h, l}, each of the same length. See web/modelspace.py.
        stops: init.stops || { r: [], au: [], t: [], h: [], l: [] },
        home: init.home || 0,
        cahoy: init.cahoy || [],
        // Per-planet numbers only; the wording is joined on from WHATIF_TEXT above.
        whatif: (init.whatif || []).map(function (v) {
          return {
            id: v.id, h: v.h, l: v.l, de: v.de,
            label: textFor(v.id).label, detail: textFor(v.id).detail,
          };
        }),
        year: init.year || null,
        measuredBase: !!init.measuredBase,
        radius: init.radius || 8,
        cloudState: init.cloudState || "",
        planetHex: init.planetHex || "#888888",

        idx: 0,          // slider position, integer index into stops
        frac: 0,         // fractional offset while the colour year is playing
        playing: false,
        info: "",        // which ℹ explainer is open ("move" | "year" | "whatif")
        picked: null,    // selected what-if variant id, null = the planet as modelled
        _raf: null,
        _t0: 0,
        _lastPaint: "",   // last hex actually drawn, so repaints of the same colour are free

        init() {
          this.idx = this.home;
          this.$nextTick(() => { this.paint(); this.paintWhatIf(); });
        },

        // --- the current position -------------------------------------------------------
        n() { return this.stops.h.length; },
        clamp(i) { return Math.max(0, Math.min(this.n() - 1, i)); },
        pos() { return this.idx + this.frac; },
        iLo() { return this.clamp(Math.floor(this.pos())); },
        iHi() { return this.clamp(Math.ceil(this.pos())); },
        t() { return this.pos() - Math.floor(this.pos()); },
        /* Linear blend of one parallel array between the two bracketing stops. */
        lerp(key) {
          var a = this.stops[key][this.iLo()], b = this.stops[key][this.iHi()];
          if (a == null) return null;
          if (b == null) b = a;
          return a + (b - a) * this.t();
        },

        hex() { return mixHex(this.stops.h[this.iLo()], this.stops.h[this.iHi()], this.t()); },
        lum() { var v = this.lerp("l"); return v == null ? 0 : v; },
        au() {
          var a = this.stops.au[this.iLo()];
          if (a == null) return null;
          // Distance is log-spaced, so interpolate it that way — a linear mix between two
          // stops an octave apart would print a distance the colour was never computed at.
          var b = this.stops.au[this.iHi()];
          if (b == null) b = a;
          return a <= 0 || b <= 0 ? a : Math.exp(Math.log(a) + (Math.log(b) - Math.log(a)) * this.t());
        },
        temp() { var v = this.lerp("t"); return v == null ? 0 : v; },
        atHome() { return Math.abs(this.pos() - this.home) < 0.001; },

        // --- readouts -------------------------------------------------------------------
        auText() { return fmtAu(this.au()); },
        tempText() { return fmtTemp(this.temp()); },
        regimeText() { return regime(this.temp()); },
        // "3.2× further out" / "12× closer in" — the comparison a newcomer actually wants.
        moveText() {
          var r = this.stops.r[this.iLo()];
          if (r == null) r = 1;
          if (this.atHome()) return "where it really is";
          var f = r >= 1 ? r : 1 / r;
          var n = f >= 100 ? Math.round(f).toLocaleString() : f.toFixed(f < 10 ? 1 : 0);
          return n + "× " + (r >= 1 ? "further out" : "closer in");
        },
        lumText() { return (this.lum() * 100).toFixed(1) + "%"; },

        // --- interactions ---------------------------------------------------------------
        moved() { this.stopYear(); this.frac = 0; this.paint(); },
        goHome() { this.stopYear(); this.idx = this.home; this.frac = 0; this.paint(); },
        toggleInfo(k) { this.info = this.info === k ? "" : k; },

        /* Jump the slider to a Cahoy grid distance, so the two models can be read against
         * each other at the same place rather than by eye across the control. */
        gotoCahoy(c) {
          var best = 0, bestD = Infinity;
          for (var i = 0; i < this.n(); i++) {
            var d = Math.abs(Math.log(this.stops.r[i]) - Math.log(c.r));
            if (d < bestD) { bestD = d; best = i; }
          }
          this.stopYear();
          this.idx = best; this.frac = 0;
          this.paint();
        },
        /* Where a grid mark sits along the slider, as a percentage of its width. */
        cahoyPct(c) {
          var lo = Math.log(this.stops.r[0]), hi = Math.log(this.stops.r[this.n() - 1]);
          return (100 * (Math.log(c.r) - lo) / (hi - lo)).toFixed(2) + "%";
        },
        homePct() {
          return (100 * this.home / Math.max(1, this.n() - 1)).toFixed(2) + "%";
        },

        // --- the colour year ------------------------------------------------------------
        /* One orbit in 12 s of wall clock, sampled at equal steps of TIME. The planet
         * therefore loiters through the cold outer stretch and whips through periastron,
         * which is the honest shape of an eccentric year and the thing worth watching. */
        toggleYear() { this.playing ? this.stopYear() : this.startYear(); },
        startYear() {
          if (!this.year || this.playing) return;
          this.playing = true;
          this._t0 = 0;
          var self = this;
          var lastFrame = 0;
          var step = function (now) {
            if (!self.playing) return;
            // Reschedule BEFORE doing any work: a throw or a slow frame in the repaint below
            // must never be able to leave the loop dead with `playing` still true.
            self._raf = requestAnimationFrame(step);
            // A WebGL repaint costs ~13 ms and the page hero is already spinning its own, so
            // running this at display rate starves the frame budget and stalls the tab. One
            // orbit takes 12 s; 20 fps is far more resolution than that motion needs.
            if (now - lastFrame < 50) return;
            lastFrame = now;
            if (!self._t0) self._t0 = now;
            var pos = self.year.pos;
            var phase = (((now - self._t0) / 12000) % 1) * pos.length;
            var i = Math.floor(phase), f = phase - i;
            var a = pos[i % pos.length], b = pos[(i + 1) % pos.length];
            var track = a + (b - a) * f;
            self.idx = Math.floor(track);
            self.frac = track - self.idx;
            self.paint();
          };
          this._raf = requestAnimationFrame(step);
        },
        stopYear() {
          this.playing = false;
          if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
        },
        /* Fraction of the orbit the planet spends near periastron, as plain English. */
        hotText() {
          if (!this.year) return "";
          var pct = this.year.hot * 100;
          return pct < 1 ? "under 1% of its year" : Math.round(pct) + "% of its year";
        },

        // --- what-if --------------------------------------------------------------------
        pick(id) { this.picked = this.picked === id ? null : id; this.paintWhatIf(); },
        current() {
          var self = this;
          return this.whatif.filter(function (v) { return v.id === self.picked; })[0] || null;
        },
        whatIfHex() { var v = this.current(); return v ? v.h : this.planetHex; },
        whatIfLabel() { var v = this.current(); return v ? v.label : "As modelled"; },
        whatIfDetail() {
          var v = this.current();
          return v ? v.detail
            : "The assumptions the pipeline actually used for this planet. Pick one of the " +
              "others to see how far the colour moves when that assumption changes.";
        },
        whatIfDe() { var v = this.current(); return v ? v.de : 0; },
        /* How to read a ΔE, in words rather than as a bare number. */
        deText() {
          var de = this.whatIfDe();
          if (!this.picked) return "this planet's own assumptions";
          if (de < 1) return "no visible difference";
          if (de < 2) return "barely visible";
          if (de < 10) return "clearly a different colour";
          return "a completely different colour";
        },

        // --- rendering ------------------------------------------------------------------
        /* A repaint costs ~13 ms, and both callers can fire far faster than that: a slider
         * drag emits input events at display rate, and the colour year ticks 20 times a
         * second. The colour itself only takes 25 distinct values across the whole track, so
         * skipping repaints that would draw the same disc again is nearly all of the work. */
        paint() {
          if (!window.PlanetRender || !this.$refs.msCanvas) return;
          var hex = this.hex();
          if (hex === this._lastPaint) return;
          this._lastPaint = hex;
          window.PlanetRender.render(this.$refs.msCanvas, {
            palette: window.PlanetRender.ramp(hex),
            baseHex: hex,
            radius: this.radius,
            cloudState: this.cloudState,
            lumY: this.lum(),
            style: "smooth",
          });
        },
        paintWhatIf() {
          if (!window.PlanetRender || !this.$refs.wiCanvas) return;
          var v = this.current();
          var hex = v ? v.h : this.planetHex;
          window.PlanetRender.render(this.$refs.wiCanvas, {
            palette: window.PlanetRender.ramp(hex),
            baseHex: hex,
            radius: this.radius,
            cloudState: this.cloudState,
            lumY: v ? v.l : null,
            style: "smooth",
          });
        },
        destroy() { this.stopYear(); },
      };
    });
  });
})();
