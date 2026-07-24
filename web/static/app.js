// Alpine components + the gallery hold-to-peek. No build step; plain ES.

document.addEventListener("alpine:init", () => {

  // Gallery: search / filter / sort over the inlined index (window.PLANETS).
  // Cards are server-rendered; this toggles their visibility and CSS `order`.
  Alpine.data("gallery", () => ({
    q: "",
    prov: "all",
    sort: "name",
    scrolled: false,  // page scrolled past the header: toolbar is stuck, TOP button shows
    // Labels for the custom (retro) dropdowns.
    provLabels: {
      all: "All", model: "Modelled", "simulated-cgi": "Roman: simulated",
      "measured-cgi": "Roman: measured", "model-microlensing": "Microlensing",
    },
    sortLabels: {
      name: "Sort: name", temp: "Sort: hottest", lum: "Sort: brightest",
      dist: "Sort: nearest Earth", de: "Sort: colour lost to Roman",
    },
    // Colour exploration: a family-chip filter + a "similar to this planet" perceptual sort.
    family: null,   // selected colour-family chip (e.g. "blue"), or null for all
    nearId: null,   // "similar colour to this planet" reference id, or null
    familyMeta: {
      blue: { n: "Blue", c: "#4a7fd0" }, teal: { n: "Teal", c: "#2fb8b8" },
      green: { n: "Green", c: "#4caf6a" }, gold: { n: "Gold", c: "#d9b44a" },
      orange: { n: "Orange", c: "#e08a3c" }, red: { n: "Red", c: "#d0503c" },
      pink: { n: "Pink", c: "#d06a9c" }, brown: { n: "Brown", c: "#8a6a4a" },
      grey: { n: "Grey", c: "#9aa0ac" }, white: { n: "White", c: "#dfe3ea" },
      dark: { n: "Dark", c: "#3a3f4a" },
    },
    familyOrder: ["blue", "teal", "green", "gold", "orange", "red", "pink", "brown", "grey", "white", "dark"],
    // Card render style: "smooth" (sphere) or "retro" (pixel). Persisted, default pixel.
    style: localStorage.getItem("planetStyle") || "retro",
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
    // Accent theme, persisted and applied site-wide via a data-attribute on <html>.
    accent: localStorage.getItem("accent") || "blue",
    // Retro accent palettes (id must match CSS [data-accent] + .acc-<id>).
    accents: [
      { id: "blue", name: "Cobalt" },
      { id: "electric", name: "Electric" },
      { id: "ice", name: "Ice" },
      { id: "tron", name: "Tron" },
      { id: "cyan", name: "Teletext" },
      { id: "seafoam", name: "Seafoam" },
      { id: "green", name: "Phosphor" },
      { id: "mustard", name: "Gold" },
      { id: "amber", name: "Amber" },
      { id: "pink", name: "Synthwave" },
      { id: "violet", name: "Vaporwave" },
    ],
    setAccent(a) {
      this.accent = a;
      try { localStorage.setItem("accent", a); } catch (e) { /* ignore */ }
      document.documentElement.setAttribute("data-accent", a);
    },
    setStyle(s) {
      this.style = s;
      try { localStorage.setItem("planetStyle", s); } catch (e) { /* ignore */ }
      this.renderCards();
    },
    setFidelity(f) {
      this.fidelity = f;
      try { localStorage.setItem("renderFidelity", f); } catch (e) { /* ignore */ }
      this.renderCards();
    },
    // Clicking either side of a two-state toggle flips it — including the already-active side.
    toggleStyle() { this.setStyle(this.style === "retro" ? "smooth" : "retro"); },
    toggleFidelity() { this.setFidelity(this.fidelity === "classic" ? "stylised" : "classic"); },
    // Deep-link support: /?near=<id> (similar-colour sort) and /?family=<f> (colour filter).
    init() {
      const p = new URLSearchParams(location.search);
      const near = p.get("near");
      if (near) this.nearId = near;
      const fam = p.get("family");
      if (fam && this.familyMeta[fam]) this.family = fam;
    },
    // Colour families actually present in the data, in canonical order, with a swatch + label.
    families() {
      const present = new Set((window.PLANETS || []).map((x) => x.family));
      return this.familyOrder.filter((f) => present.has(f))
        .map((f) => ({ id: f, name: this.familyMeta[f].n, colour: this.familyMeta[f].c }));
    },
    // Provenance dropdown: "all" + only the provenances present (declutters at scale, where
    // it's nearly all "Modelled" but the handful of Roman targets are still worth finding).
    provOptions() {
      const present = new Set((window.PLANETS || []).map((x) => x.prov));
      return Object.entries(this.provLabels).filter(([v]) => v === "all" || present.has(v));
    },
    setFamily(f) { this.family = this.family === f ? null : f; },
    setSort(v) { this.sort = v; this.nearId = null; },  // an explicit sort cancels similar-colour
    clearNear() { this.nearId = null; },
    nearName() {
      const p = (window.PLANETS || []).find((x) => x.id === this.nearId);
      return p ? p.name : "";
    },
    nearHex() {
      const p = (window.PLANETS || []).find((x) => x.id === this.nearId);
      return p ? p.hex : "#000";
    },
    // Perceptual colour distance (ΔE76 over CIE Lab), computed from the displayed hex so it
    // matches exactly what the eye sees. Cheap enough to run over the whole set on each sort.
    _lab(hex) {
      const h = hex.replace("#", "");
      const toLin = (c) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
      const r = toLin(parseInt(h.slice(0, 2), 16) / 255);
      const g = toLin(parseInt(h.slice(2, 4), 16) / 255);
      const b = toLin(parseInt(h.slice(4, 6), 16) / 255);
      let X = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047;
      const Y = r * 0.2126 + g * 0.7152 + b * 0.0722;
      let Z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883;
      const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
      const fx = f(X), fy = f(Y), fz = f(Z);
      return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
    },
    _de(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); },
    renderCards() {
      if (!window.PlanetRender || !window.PLANETS) return;
      var byId = {};
      window.PLANETS.forEach((p) => (byId[p.id] = p));
      var style = this.style, fidelity = this.fidelity;
      document.querySelectorAll(".card-planet").forEach((cv) => {
        var p = byId[cv.dataset.id];
        if (!p) return;
        cv.classList.toggle("pixel", style === "retro");
        window.PlanetRender.render(cv, {
          palette: p.palette, radius: p.radius, cloudState: p.cloud, lumY: p.lum,
          style: style, fidelity: fidelity,
        });
      });
    },
    get view() {
      let items = (window.PLANETS || []).filter((p) => {
        if (this.prov !== "all" && p.prov !== this.prov) return false;
        if (this.family && p.family !== this.family) return false;
        if (this.q) {
          const s = (p.name + " " + p.host).toLowerCase();
          if (!s.includes(this.q.toLowerCase())) return false;
        }
        return true;
      });
      const ref = this.nearId && (window.PLANETS || []).find((x) => x.id === this.nearId);
      if (ref) {
        // Similar-colour sort: rank by perceptual distance to the reference planet's colour.
        const rl = this._lab(ref.hex), dc = {};
        const dist = (p) => (dc[p.id] ??= this._de(this._lab(p.hex), rl));
        items.sort((a, b) => dist(a) - dist(b));
      } else {
        const s = this.sort;
        items.sort((a, b) => {
          if (s === "name") return a.name.localeCompare(b.name);
          if (s === "temp") return (b.temp || 0) - (a.temp || 0);
          if (s === "lum") return (b.lum || 0) - (a.lum || 0);
          if (s === "dist") return (a.dist ?? Infinity) - (b.dist ?? Infinity); // nearest, unknowns last
          if (s === "de") return (b.de || 0) - (a.de || 0);
          return 0;
        });
      }
      const vis = new Set(items.map((p) => p.id));
      const ord = {};
      items.forEach((p, i) => (ord[p.id] = i));
      return { vis, ord, count: items.length };
    },
    show(id) {
      return this.view.vis.has(id);
    },
    order(id) {
      const o = this.view.ord[id];
      return o === undefined ? 999 : o;
    },
    count() {
      return this.view.count;
    },
  }));

  // Detail: full-spectrum <-> Roman toggle + palette export. Neither view is "true colour":
  // both are modelled. `init` carries the precomputed colours/palettes.
  Alpine.data("detail", (init) => ({
    view: "full",
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
    heroStyle: "retro",   // hero render: "retro" (pixel) or "smooth" (sphere)
    heroSource: "model",  // hero shows the "model" render or the real "telescope" image
    obs: [],              // real telescope images for this planet (0+), injected by init
    obsIdx: 0,            // which telescope image is selected (when >1 exist)
    obsZoom: false,       // real-image lightbox open?
    msg: "",
    help: false,       // dossier "how to read this" expandable (ℹ button)
    info: null,        // which scope explainer is open: 'view' | 'style' | 'source' | null
    panel: "palette",  // mobile-only: which info panel shows ('readout' | 'palette' | 'data')
    descOpen: false,   // mobile-only: caption under the planet name expanded?
    ledFlash: false,   // channel LED blink on view change
    _t: null,
    _lt: null,
    ...init,
    // Carry the scope's settings across same-system hops (each planet is its own page).
    // Every option falls back gracefully when the target planet can't honour it.
    init() {
      const v = localStorage.getItem("scopeView");
      if (v === "full" || v === "roman") this.view = v;
      // Shape shares the gallery's Sphere/Pixel key so both pages always agree.
      const hs = localStorage.getItem("planetStyle");
      if (hs === "retro" || hs === "smooth") this.heroStyle = hs;
      // Keep the same telescope selected if this planet was imaged by it too.
      const tel = localStorage.getItem("obsTelescope");
      if (tel) { const j = this.obs.findIndex((o) => o.telescope === tel); if (j >= 0) this.obsIdx = j; }
      // The real photo persists only across planet-to-planet hops (same-system links);
      // arriving from the gallery or a fresh visit always opens on the modelled render.
      const src = localStorage.getItem("heroSource");
      const fromPlanet = document.referrer.includes("/planet/");
      this.heroSource =
        src === "telescope" && fromPlanet && this.obs.length ? "telescope" : "model";
    },
    _persist(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
    blink() {
      this.ledFlash = true;
      clearTimeout(this._lt);
      this._lt = setTimeout(() => (this.ledFlash = false), 320);
    },
    // Scope controls: every knob/button drives real state (and persists across hops):
    setView(v) { this.view = v; this._persist("scopeView", v); this.blink(); },
    selectObs(i) { this.obsIdx = i; this._persist("obsTelescope", this.curObs().telescope || ""); },
    // Style/Shape act on the modelled render. If the real photo is showing, the first click
    // simply brings the model back (no value change) so the knobs never feel "locked out";
    // a further click then toggles. This is why turning to Telescope doesn't trap you there.
    toggleFidelity() {
      if (this.heroSource === "telescope") { this.heroSource = "model"; this._persist("heroSource", "model"); this.blink(); this.renderAll(); return; }
      this.setFidelity(this.fidelity === "classic" ? "stylised" : "classic");
    },
    toggleHeroStyle() {
      if (this.heroSource === "telescope") { this.heroSource = "model"; this._persist("heroSource", "model"); this.blink(); this.renderAll(); return; }
      this.heroStyle = this.heroStyle === "retro" ? "smooth" : "retro";
      this._persist("planetStyle", this.heroStyle);
      this.renderAll();
    },
    // The currently-selected real image (safe when none exist).
    curObs() { return this.obs[this.obsIdx] || {}; },
    // Flip the hero between the modelled render and the real telescope photo (only present
    // for directly-imaged planets; the knob is not rendered otherwise).
    toggleHeroSource() {
      if (!this.obs.length) return;
      this.heroSource = this.heroSource === "model" ? "telescope" : "model";
      this._persist("heroSource", this.heroSource);
      this.blink();
    },
    toggleInfo(k) { this.info = this.info === k ? null : k; },
    setFidelity(f) {
      this.fidelity = f;
      try { localStorage.setItem("renderFidelity", f); } catch (e) { /* ignore */ }
      this.renderAll();
    },
    flash(m) {
      this.msg = m;
      clearTimeout(this._t);
      this._t = setTimeout(() => (this.msg = ""), 1600);
    },
    copy(hex) {
      navigator.clipboard?.writeText(hex);
      this.flash("copied " + hex);
    },
    // All five stops of the current view's palette, comma-joined (dark -> light);
    // single stops are click-to-copy on the chips, CSS vars / .ASE cover the rest.
    copyAll() {
      const pal = this.view === "full" ? this.fullPalette : this.romanPalette;
      navigator.clipboard?.writeText(pal.join(", "));
      this.flash("copied all " + pal.length + " colours");
    },
    copyCssVars() {
      const pal = this.view === "full" ? this.fullPalette : this.romanPalette;
      const roles = ["shade-2", "shade-1", "base", "tint-1", "tint-2"];
      const lines = pal.map((h, i) => `  --planet-${roles[i] || i}: ${h};`);
      const css = ":root {\n" + lines.join("\n") + "\n}";
      navigator.clipboard?.writeText(css);
      this.flash("copied CSS variables");
    },
    // Render the three planet visualisations from the CURRENT view's palette + attributes.
    renderAll() {
      if (!window.PlanetRender || !this.$refs.cHero) return;
      const opts = {
        palette: this.view === "full" ? this.fullPalette : this.romanPalette,
        radius: this.radius,
        cloudState: this.cloudState,
        lumY: this.view === "full" ? this.fullLum : this.romanLum,
        fidelity: this.fidelity,
      };
      // Single hero planet, rotating; its style (sphere/pixel) is a scope knob.
      this.$refs.cHero.classList.toggle("pixel", this.heroStyle === "retro");
      PlanetRender.spin(this.$refs.cHero, { ...opts, style: this.heroStyle });
    },
  }));
});

// Card interaction: a normal click/tap navigates to the full planet page (the <a href>);
// press-and-HOLD (~450ms, held still) shows a lightweight peek (name, caption, plot) that
// stays up only while the press is held and vanishes on release. Works with mouse + touch.
//
// Robustness: the click decision is DURATION-based and only ever cancels navigation for a
// genuine long, still press on the same card. Every short/normal click falls through to the
// browser's default <a href> navigation and is never prevented, so clicks always work.
(function () {
  var LP_MS = 450, MOVE_TOL = 12;
  var downCard = null, downAt = 0, sx = 0, sy = 0, moved = false, timer = null;
  var cache = {};  // peek url -> Promise<html>; fragments are static, cache for the session

  function fetchPeek(url) {
    if (!url) return null;
    if (!cache[url]) cache[url] = fetch(url).then(function (r) { return r.text(); });
    return cache[url];
  }
  function showPeek(card) {
    var peek = document.getElementById("peek"), body = document.getElementById("peek-body");
    var p = peek && fetchPeek(card.getAttribute("data-peek"));
    if (!p) return;
    p.then(function (html) {
      // Only if this press is still being held on the same card.
      if (downCard !== card) return;
      body.innerHTML = html;
      // The planet itself, drawn with the same engine + settings as the gallery cards.
      var cv = body.querySelector(".peek-planet");
      var pl = cv && window.PlanetRender && (window.PLANETS || []).find(function (x) {
        return x.id === cv.dataset.id;
      });
      if (pl) {
        var style = localStorage.getItem("planetStyle") || "retro";
        cv.classList.toggle("pixel", style === "retro");
        window.PlanetRender.render(cv, {
          palette: pl.palette, radius: pl.radius, cloudState: pl.cloud, lumY: pl.lum,
          style: style, fidelity: localStorage.getItem("renderFidelity") || "classic",
        });
      }
      peek.classList.add("on");
    });
  }
  function hidePeek() {
    var peek = document.getElementById("peek");
    if (peek) peek.classList.remove("on");
  }

  var pending = null;  // one-shot {card,longpress} set on release, consumed by the next click

  document.addEventListener("pointerdown", function (e) {
    var card = e.target.closest && e.target.closest("a.card");
    downCard = card; downAt = Date.now(); moved = false; sx = e.clientX; sy = e.clientY;
    clearTimeout(timer);
    if (card) {
      fetchPeek(card.getAttribute("data-peek"));  // warm the cache during the press
      timer = setTimeout(function () { if (!moved && downCard === card) showPeek(card); }, LP_MS);
    }
  }, true);
  document.addEventListener("pointermove", function (e) {
    if (downCard && (Math.abs(e.clientX - sx) > MOVE_TOL || Math.abs(e.clientY - sy) > MOVE_TOL)) {
      moved = true; clearTimeout(timer);
    }
  }, true);
  document.addEventListener("pointerup", function () {
    clearTimeout(timer); hidePeek();
    if (downCard) pending = { card: downCard, longpress: !moved && Date.now() - downAt >= LP_MS };
    downCard = null;
  }, true);
  document.addEventListener("pointercancel", function () {
    downCard = null; clearTimeout(timer); hidePeek();
  }, true);

  // Only a click that immediately follows a long, still press cancels navigation (the user
  // was peeking, not clicking). Any other click has no pending long-press -> navigates.
  document.addEventListener("click", function (e) {
    var card = e.target.closest && e.target.closest("a.card");
    var p = pending; pending = null;
    if (card && p && p.card === card && p.longpress) {
      e.preventDefault(); e.stopPropagation();
    }
  }, true);
  document.addEventListener("contextmenu", function (e) {
    if (e.target.closest && e.target.closest("a.card")) e.preventDefault();
  });
})();

// Hover-to-spin on gallery cards (desktop with a real pointer only, avoids mobile churn
// and keeps the site light: only the hovered planet animates).
(function () {
  if (!window.matchMedia || !window.matchMedia("(hover: hover)").matches) return;
  var hovered = null;
  function optsFor(cv) {
    var list = window.PLANETS || [];
    var p = null;
    for (var i = 0; i < list.length; i++) if (list[i].id === cv.dataset.id) { p = list[i]; break; }
    if (!p) return null;
    return {
      palette: p.palette, radius: p.radius, cloudState: p.cloud, lumY: p.lum,
      style: localStorage.getItem("planetStyle") || "retro",
      fidelity: localStorage.getItem("renderFidelity") || "classic",
    };
  }
  document.addEventListener("mouseover", function (e) {
    var card = e.target.closest && e.target.closest("a.card");
    if (card === hovered) return;
    if (hovered && window.PlanetRender) {
      var pc = hovered.querySelector(".card-planet");
      if (pc) { window.PlanetRender.stop(pc); var o0 = optsFor(pc); if (o0) window.PlanetRender.render(pc, o0); }
    }
    hovered = card;
    if (card && window.PlanetRender) {
      var cv = card.querySelector(".card-planet");
      var o = cv && optsFor(cv);
      if (o) window.PlanetRender.spin(cv, o);
    }
  });
})();
