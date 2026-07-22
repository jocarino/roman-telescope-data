// Alpine components + the htmx->drawer bridge. No build step; plain ES.

document.addEventListener("alpine:init", () => {
  Alpine.store("drawer", { open: false });

  // Gallery: search / filter / sort over the inlined index (window.PLANETS).
  // Cards are server-rendered; this toggles their visibility and CSS `order`.
  Alpine.data("gallery", () => ({
    q: "",
    prov: "all",
    sort: "name",
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
    msg: "",
    _t: null,
    ...init,
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
    window.scrollTo({ top: 0 });
  }
});
