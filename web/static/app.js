// Alpine components + the htmx->drawer bridge. No build step; plain ES.

document.addEventListener("alpine:init", () => {
  Alpine.store("drawer", { open: false });

  // Gallery: search / filter / sort over the inlined index (window.PLANETS).
  // Cards are server-rendered; this toggles their visibility and CSS `order`.
  Alpine.data("gallery", () => ({
    q: "",
    prov: "all",
    sort: "name",
    // Card render style: "smooth" (sphere) or "retro" (pixel). Persisted, default sphere.
    style: localStorage.getItem("planetStyle") || "smooth",
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
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
    msg: "",
    _t: null,
    ...init,
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
      if (!window.PlanetRender || !this.$refs.cSmooth) return;
      const opts = {
        palette: this.view === "full" ? this.fullPalette : this.romanPalette,
        radius: this.radius,
        cloudState: this.cloudState,
        lumY: this.view === "full" ? this.fullLum : this.romanLum,
        fidelity: this.fidelity,
      };
      PlanetRender.render(this.$refs.cSmooth, { ...opts, style: "smooth" });
      PlanetRender.render(this.$refs.cRetro, { ...opts, style: "retro" });
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
