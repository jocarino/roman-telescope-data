// Alpine components + the htmx->drawer bridge. No build step; plain ES.

document.addEventListener("alpine:init", () => {
  Alpine.store("drawer", { open: false });

  // Gallery: search / filter / sort over the inlined index (window.PLANETS).
  // Cards are server-rendered; this toggles their visibility and CSS `order`.
  Alpine.data("gallery", () => ({
    q: "",
    prov: "all",
    sort: "name",
    // Labels for the custom (retro) dropdowns.
    provLabels: {
      all: "All provenance", model: "Model", "simulated-cgi": "Roman: simulated",
      "measured-cgi": "Roman: measured", "model-microlensing": "Microlensing",
    },
    sortLabels: {
      name: "Sort: name", temp: "Sort: hottest", lum: "Sort: brightest",
      de: "Sort: colour lost to Roman",
    },
    // Card render style: "smooth" (sphere) or "retro" (pixel). Persisted, default pixel.
    style: localStorage.getItem("planetStyle") || "retro",
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
    // Accent theme, persisted and applied site-wide via a data-attribute on <html>.
    accent: localStorage.getItem("accent") || "blue",
    // Retro accent palettes (id must match CSS [data-accent] + .acc-<id>).
    accents: [
      { id: "blue", name: "Cobalt" },
      { id: "mustard", name: "Gold" },
      { id: "green", name: "Phosphor" },
      { id: "amber", name: "Amber" },
      { id: "pink", name: "Synthwave" },
      { id: "cyan", name: "Teletext" },
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
        if (this.q) {
          const s = (p.name + " " + p.host).toLowerCase();
          if (!s.includes(this.q.toLowerCase())) return false;
        }
        return true;
      });
      const s = this.sort;
      items.sort((a, b) => {
        if (s === "name") return a.name.localeCompare(b.name);
        if (s === "temp") return (b.temp || 0) - (a.temp || 0);
        if (s === "lum") return (b.lum || 0) - (a.lum || 0);
        if (s === "de") return (b.de || 0) - (a.de || 0);
        return 0;
      });
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
    msg: "",
    help: false,       // dossier "how to read this" expandable (ℹ button)
    info: null,        // which scope explainer is open: 'view' | 'style' | 'source' | null
    ledFlash: false,   // channel LED blink on view change
    _t: null,
    _lt: null,
    ...init,
    blink() {
      this.ledFlash = true;
      clearTimeout(this._lt);
      this._lt = setTimeout(() => (this.ledFlash = false), 320);
    },
    // Scope controls — every knob/button drives real state:
    setView(v) { this.view = v; this.blink(); },
    toggleFidelity() { this.setFidelity(this.fidelity === "classic" ? "stylised" : "classic"); },
    toggleHeroStyle() { this.heroStyle = this.heroStyle === "retro" ? "smooth" : "retro"; this.renderAll(); },
    // Flip the hero between the modelled render and the real telescope photo (only present
    // for directly-imaged planets — the knob is not rendered otherwise).
    toggleHeroSource() { this.heroSource = this.heroSource === "model" ? "telescope" : "model"; this.blink(); },
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
    copyBase() {
      const h = this.view === "full" ? this.fullHex : this.romanHex;
      navigator.clipboard?.writeText(h);
      this.flash("copied " + h);
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

// When a detail fragment lands in the drawer, open it.
document.addEventListener("htmx:afterSwap", (e) => {
  if (e.detail && e.detail.target && e.detail.target.id === "drawer-body") {
    if (window.Alpine) Alpine.store("drawer").open = true;
  }
});

// Card interaction: a normal click/tap navigates to the full planet page (the <a href>);
// a long-press (~450ms, held still) opens the side sheet instead. Works with mouse + touch.
//
// Robustness: the click decision is DURATION-based and only ever cancels navigation for a
// genuine long, still press on the same card. Every short/normal click falls through to the
// browser's default <a href> navigation and is never prevented — so clicks always work.
(function () {
  var LP_MS = 450, MOVE_TOL = 12;
  var downCard = null, downAt = 0, sx = 0, sy = 0, moved = false, timer = null;

  function openDrawer(card) {
    var frag = card.getAttribute("data-fragment");
    if (!frag || !window.htmx) return;
    // Cache-bust so the drawer always reflects the current build (avoids stale fragments).
    window.htmx.ajax("GET", frag + "?_=" + Date.now(), "#drawer-body");
    if (window.Alpine) window.Alpine.store("drawer").open = true;
  }

  var pending = null;  // one-shot {card,longpress} set on release, consumed by the next click

  document.addEventListener("pointerdown", function (e) {
    var card = e.target.closest && e.target.closest("a.card");
    downCard = card; downAt = Date.now(); moved = false; sx = e.clientX; sy = e.clientY;
    clearTimeout(timer);
    // Open at the threshold for responsiveness while still holding.
    if (card) timer = setTimeout(function () { if (!moved && downCard === card) openDrawer(card); }, LP_MS);
  }, true);
  document.addEventListener("pointermove", function (e) {
    if (downCard && (Math.abs(e.clientX - sx) > MOVE_TOL || Math.abs(e.clientY - sy) > MOVE_TOL)) {
      moved = true; clearTimeout(timer);
    }
  }, true);
  document.addEventListener("pointerup", function () {
    clearTimeout(timer);
    if (downCard) pending = { card: downCard, longpress: !moved && Date.now() - downAt >= LP_MS };
    downCard = null;
  }, true);
  document.addEventListener("pointercancel", function () { downCard = null; clearTimeout(timer); }, true);

  // Only a click that immediately follows a long, still press cancels navigation. Any other
  // click (short press, keyboard-activated, synthetic) has no pending long-press -> navigates.
  document.addEventListener("click", function (e) {
    var card = e.target.closest && e.target.closest("a.card");
    var p = pending; pending = null;
    if (card && p && p.card === card && p.longpress) {
      e.preventDefault(); e.stopPropagation();
      openDrawer(card);
    }
  }, true);
  document.addEventListener("contextmenu", function (e) {
    if (e.target.closest && e.target.closest("a.card")) e.preventDefault();
  });
})();

// Hover-to-spin on gallery cards (desktop with a real pointer only — avoids mobile churn
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
