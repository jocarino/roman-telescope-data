// Alpine components + the gallery hold-to-peek. No build step; plain ES.

// Random-planet jump, shared by the gallery button, the detail-page button and the R key.
// `pool` is the list to roll over (e.g. the gallery's filtered results); falls back to the
// full index. Never lands on the planet already on screen (unless it's the only one).
const ExoRandom = {
  go(pool) {
    let list = (pool && pool.length ? pool : window.PLANETS) || [];
    if (!list.length) return;
    const m = location.pathname.match(/^\/planet\/([^/]+?)(?:\.html)?$/);
    const cur = m ? decodeURIComponent(m[1]) : null;
    if (cur && list.length > 1) list = list.filter((p) => p.id !== cur);
    const p = list[Math.floor(Math.random() * list.length)];
    location.href = "/planet/" + p.id;
  },
};

// Keyboard shortcut: R rolls a random planet on pages that registered a handler
// (gallery + planet detail). Ignored while typing in a field.
document.addEventListener("keydown", (e) => {
  if ((e.key !== "r" && e.key !== "R") || e.metaKey || e.ctrlKey || e.altKey) return;
  const el = document.activeElement;
  if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT" ||
    el.isContentEditable)) return;
  if (typeof window.__randomGo === "function") window.__randomGo();
});

document.addEventListener("alpine:init", () => {

  // Gallery: search / filter / sort over a fetched index (window.PLANETS). Cards are rendered
  // incrementally in JS and their planet is drawn only when scrolled into view, so the grid
  // scales to thousands of planets without a heavy server-rendered DOM or an inlined index.
  Alpine.data("gallery", (cfg) => ({
    indexUrl: (cfg && cfg.indexUrl) || null,
    loaded: false,
    _results: null,       // cached ordered+filtered array for the current render pass
    _shown: 0,            // how many cards appended to the grid so far
    _batch: 60,           // cards appended per scroll step
    _map: null,           // id -> planet lookup
    _raf: 0,              // pending rAF handle for the throttled draw pass
    _loadIO: null,        // appends the next batch as the sentinel nears the viewport
    q: "",
    prov: "all",
    ptype: "all",
    disc: "all",
    distBand: "all",
    fic: false,       // "seen in fiction" toggle: show only planets in the pop-culture overlay
    sort: "name",
    scrolled: false,  // page scrolled past the header: toolbar is stuck, TOP button shows
    // Labels for the custom (retro) dropdowns.
    provLabels: {
      all: "All", model: "Modelled", "simulated-cgi": "Roman: simulated",
      "measured-cgi": "Roman: measured", "model-microlensing": "Microlensing",
      "measured-albedo": "Spectrum: measured",
    },
    typeLabels: {
      all: "All types", rocky: "Rocky", "super-earth": "Super-Earth",
      neptune: "Neptune-like", "gas-giant": "Gas giant", "hot-jupiter": "Hot Jupiter",
      unknown: "Unknown",
    },
    // Distance bands (light-years). id -> [label, maxExclusive in ly]; last band catches the rest.
    distBands: [
      ["all", "Any distance", Infinity],
      ["near", "≤ 50 ly", 50],
      ["mid", "50–300 ly", 300],
      ["far", "300–1,500 ly", 1500],
      ["remote", "> 1,500 ly", Infinity],
    ],
    sortLabels: {
      name: "Sort: name", temp: "Sort: hottest", lum: "Sort: brightest",
      dist: "Sort: nearest Earth", de: "Sort: colour lost to Roman",
    },
    // Colour exploration: a family-chip filter + a "similar to this planet" perceptual sort.
    family: null,   // selected colour-family chip (e.g. "blue"), or null for all
    nearId: null,   // "similar colour to this planet" reference id, or null
    familyMeta: {
      teal: { n: "Teal", c: "#2fb8b8" }, azure: { n: "Azure", c: "#3ea5ff" },
      blue: { n: "Blue", c: "#4a7fd0" }, periwinkle: { n: "Periwinkle", c: "#aab6e6" },
      green: { n: "Green", c: "#4caf6a" }, gold: { n: "Gold", c: "#d9b44a" },
      orange: { n: "Orange", c: "#e08a3c" }, red: { n: "Red", c: "#d0503c" },
      pink: { n: "Pink", c: "#d06a9c" }, violet: { n: "Violet", c: "#9a7fd0" },
      brown: { n: "Brown", c: "#8a6a4a" },
      grey: { n: "Grey", c: "#9aa0ac" }, white: { n: "White", c: "#dfe3ea" },
      dark: { n: "Dark", c: "#3a3f4a" },
    },
    familyOrder: ["teal", "azure", "blue", "periwinkle", "green", "gold", "orange", "red", "pink", "violet", "brown", "grey", "white", "dark"],
    // Card render style: "smooth" (sphere) or "retro" (pixel). Persisted, default pixel.
    style: localStorage.getItem("planetStyle") || "retro",
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
    // Accent theme, persisted and applied site-wide via a data-attribute on <html>.
    accent: localStorage.getItem("accent") || "tron",
    // Retro accent palettes (id must match CSS [data-accent] + .acc-<id>), hue-ordered.
    accents: [
      { id: "blue", name: "Cobalt" },
      { id: "electric", name: "Electric" },
      { id: "ice", name: "Ice" },
      { id: "tron", name: "Tron" },
      { id: "cyan", name: "Teletext" },
      { id: "seafoam", name: "Seafoam" },
      { id: "green", name: "Phosphor" },
      { id: "lime", name: "Lime" },
      { id: "mustard", name: "Gold" },
      { id: "amber", name: "Amber" },
      { id: "ember", name: "Ember" },
      { id: "crimson", name: "Crimson" },
      { id: "pink", name: "Synthwave" },
      { id: "magenta", name: "Magenta" },
      { id: "violet", name: "Vaporwave" },
      { id: "mono", name: "Mono" },
    ],
    setAccent(a) {
      this.accent = a;
      try { localStorage.setItem("accent", a); } catch (e) { /* ignore */ }
      document.documentElement.setAttribute("data-accent", a);
    },
    setStyle(s) {
      this.style = s;
      try { localStorage.setItem("planetStyle", s); } catch (e) { /* ignore */ }
      this._redrawAll();
    },
    setFidelity(f) {
      this.fidelity = f;
      try { localStorage.setItem("renderFidelity", f); } catch (e) { /* ignore */ }
      this._redrawAll();
    },
    // Clicking either side of a two-state toggle flips it — including the already-active side.
    toggleStyle() { this.setStyle(this.style === "retro" ? "smooth" : "retro"); },
    toggleFidelity() { this.setFidelity(this.fidelity === "classic" ? "stylised" : "classic"); },
    // Fetch the index, wire up lazy rendering, and honour /?near= and /?family= deep links.
    async init() {
      const params = new URLSearchParams(location.search);
      const near = params.get("near");
      if (near) this.nearId = near;
      const fam = params.get("family");
      if (fam && this.familyMeta[fam]) this.family = fam;
      if (params.get("fiction") === "1") this.fic = true;

      try {
        const res = await fetch(this.indexUrl);
        window.PLANETS = await res.json();
      } catch (e) { window.PLANETS = []; }
      this._map = {};
      window.PLANETS.forEach((p) => (this._map[p.id] = p));
      this.loaded = true;

      // Append the next batch as the sentinel nears the viewport (infinite scroll).
      this._loadIO = new IntersectionObserver((entries) => {
        if (entries.some((e) => e.isIntersecting)) this._fill();
      }, { rootMargin: "800px" });
      this._loadIO.observe(this.$refs.sentinel);

      // Draw each planet lazily: a rAF-throttled pass draws in-viewport, not-yet-drawn cards.
      const onScroll = () => {
        if (this._raf) return;
        this._raf = requestAnimationFrame(() => { this._raf = 0; this._drawVisible(); });
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onScroll, { passive: true });

      // Any filter/sort change re-renders the grid from the top.
      ["q", "prov", "ptype", "disc", "distBand", "family", "fic", "sort", "nearId"].forEach((k) =>
        this.$watch(k, () => this._rerender()));

      window.__randomGo = () => this.randomGo();  // wire the R shortcut to this gallery

      this._rerender();
    },
    // Jump to a random planet — within the current filters (far more delightful than fully
    // random), falling back to the whole catalog when the filter matches nothing.
    randomGo() {
      if (!this.loaded) return;
      ExoRandom.go(this._results && this._results.length ? this._results : window.PLANETS);
    },
    // --- Incremental grid rendering ---------------------------------------------------------
    _rerender() {
      if (!this.loaded) return;
      window.scrollTo(0, 0);  // results changed: show them from the top, not mid-scroll
      this._results = this.results();
      this.$refs.grid.replaceChildren();
      this._shown = 0;
      this._fill();
    },
    // Append batches until the sentinel is pushed out of the pre-load zone (or results run out).
    _fill() {
      if (!this.loaded || !this._results) return;
      if (this._shown >= this._results.length) return;
      this._appendBatch();
      requestAnimationFrame(() => {
        if (this._shown >= this._results.length) return;
        const r = this.$refs.sentinel.getBoundingClientRect();
        if (r.top < window.innerHeight + 800) this._fill();
      });
    },
    _appendBatch() {
      if (!this.loaded || !this._results) return;
      const next = this._results.slice(this._shown, this._shown + this._batch);
      if (!next.length) return;
      const frag = document.createDocumentFragment();
      next.forEach((p) => frag.appendChild(this._makeCard(p)));
      this.$refs.grid.appendChild(frag);
      this._shown += next.length;
      this._drawVisible();
    },
    // Draw any appended card whose planet isn't drawn yet and is within ~a screen of the viewport.
    _drawVisible() {
      if (!window.PlanetRender || !this.$refs.grid) return;
      const pad = window.innerHeight;
      this.$refs.grid.querySelectorAll(".card-planet:not([data-drawn])").forEach((cv) => {
        const r = cv.getBoundingClientRect();
        if (r.bottom > -pad && r.top < window.innerHeight + pad) {
          this._drawCanvas(cv);
          cv.dataset.drawn = "1";
        }
      });
    },
    _makeCard(p) {
      const a = document.createElement("a");
      a.className = "card";
      a.href = "/planet/" + p.id;
      a.setAttribute("data-peek", "/fragments/peek/" + p.id + ".html");
      const cv = document.createElement("canvas");
      cv.className = "card-planet" + (this.style === "retro" ? " pixel" : "");
      cv.width = 256; cv.height = 256; cv.dataset.id = p.id;
      cv.setAttribute("aria-label", p.name + " render");
      a.appendChild(cv);
      const name = document.createElement("div");
      name.className = "card-name"; name.textContent = p.name;
      a.appendChild(name);
      const meta = document.createElement("div");
      meta.className = "card-meta";
      const badge = document.createElement("span");
      badge.className = "badge " + p.prov;
      badge.textContent = this._provBadge(p.prov);
      meta.appendChild(badge);
      const hex = document.createElement("span");
      hex.className = "badge hex";
      const chip = document.createElement("i");
      chip.className = "chip"; chip.style.background = p.hex;
      hex.appendChild(chip);
      hex.appendChild(document.createTextNode(p.hex));
      meta.appendChild(hex);
      a.appendChild(meta);
      return a;
    },
    _provBadge(prov) {
      const m = {
        model: "Modelled", "model-microlensing": "Modelled",
        "simulated-cgi": "Roman: simulated", "measured-cgi": "Roman: measured",
        "measured-hwo": "HWO: measured", "measured-albedo": "Spectrum: measured",
      };
      return m[prov] || prov;
    },
    _drawCanvas(cv) {
      const p = this._map[cv.dataset.id];
      if (!p || !window.PlanetRender) return;
      cv.classList.toggle("pixel", this.style === "retro");
      window.PlanetRender.render(cv, {
        palette: p.palette, radius: p.radius, cloudState: p.cloud, lumY: p.lum,
        style: this.style, fidelity: this.fidelity,
        phase: window.PlanetRender.hashPhase(p.id),
      });
    },
    _redrawAll() {
      if (!this.$refs.grid) return;
      // Style/fidelity changed: invalidate every card, redraw the visible ones now, rest on scroll.
      this.$refs.grid.querySelectorAll(".card-planet").forEach((cv) => cv.removeAttribute("data-drawn"));
      this._drawVisible();
    },
    // Colour families actually present in the data, in canonical order, with a swatch + label.
    // (The `this.loaded` read makes these reactive to the async fetch populating window.PLANETS.)
    families() {
      if (!this.loaded) return [];
      const present = new Set(window.PLANETS.map((x) => x.family));
      return this.familyOrder.filter((f) => present.has(f))
        .map((f) => ({ id: f, name: this.familyMeta[f].n, colour: this.familyMeta[f].c }));
    },
    // Provenance dropdown: "all" + only the provenances present, each with its planet count.
    // The counts are load-bearing UX at scale: 5,755 of 5,759 planets are "Modelled", so
    // picking it barely changes the grid — without the number the filter looks broken.
    provOptions() {
      if (!this.loaded) return [["all", this.provLabels.all]];
      const counts = {};
      window.PLANETS.forEach((x) => (counts[x.prov] = (counts[x.prov] || 0) + 1));
      return Object.entries(this.provLabels)
        .filter(([v]) => v === "all" || counts[v])
        .map(([v, label]) =>
          [v, v === "all" ? label : label + " · " + counts[v].toLocaleString()]);
    },
    // Type dropdown options: always "all", then only the types actually present in the data.
    typeOptions() {
      if (!this.loaded) return [["all", this.typeLabels.all]];
      const present = new Set(window.PLANETS.map((x) => x.ptype));
      const order = ["rocky", "super-earth", "neptune", "gas-giant", "hot-jupiter", "unknown"];
      return [["all", this.typeLabels.all], ...order.filter((t) => present.has(t))
        .map((t) => [t, this.typeLabels[t]])];
    },
    // Discovery-method dropdown: "all" + only the methods present, most-common first.
    discOptions() {
      if (!this.loaded) return [["all", "All methods"]];
      const counts = {};
      window.PLANETS.forEach((p) => { if (p.disc) counts[p.disc] = (counts[p.disc] || 0) + 1; });
      const methods = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
      return [["all", "All methods"], ...methods.map((m) => [m, m])];
    },
    // Which distance band a light-year value falls in (first matching band by ascending max).
    _distBandOf(ly) {
      if (ly == null) return "unknown";
      for (const [id, , max] of this.distBands) {
        if (id === "all" || id === "remote") continue;
        if (ly <= max) return id;
      }
      return "remote";
    },
    distBandLabel() {
      const b = this.distBands.find((x) => x[0] === this.distBand);
      return b ? b[1] : "Any distance";
    },
    // How many planets carry a fiction reference (for the "seen in fiction" toggle's counter).
    // Touch `loaded` so Alpine re-evaluates this once the (non-reactive) index has been fetched.
    ficCount() { return this.loaded ? (window.PLANETS || []).reduce((n, p) => n + (p.fic ? 1 : 0), 0) : 0; },
    setFamily(f) { this.family = this.family === f ? null : f; },
    setSort(v) { this.sort = v; this.nearId = null; },  // an explicit sort cancels similar-colour
    clearNear() { this.nearId = null; },
    nearName() {
      if (!this.loaded) return "";
      const p = window.PLANETS.find((x) => x.id === this.nearId);
      return p ? p.name : "";
    },
    nearHex() {
      if (!this.loaded) return "#000";
      const p = window.PLANETS.find((x) => x.id === this.nearId);
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
    // The filtered + sorted planet list for the current controls (an ordered array).
    results() {
      const all = window.PLANETS || [];
      let items = all.filter((p) => {
        if (this.prov !== "all" && p.prov !== this.prov) return false;
        if (this.ptype !== "all" && p.ptype !== this.ptype) return false;
        if (this.disc !== "all" && p.disc !== this.disc) return false;
        if (this.distBand !== "all" && this._distBandOf(p.dist_ly) !== this.distBand) return false;
        if (this.family && p.family !== this.family) return false;
        if (this.fic && !p.fic) return false;
        if (this.q) {
          const s = (p.name + " " + p.host).toLowerCase();
          if (!s.includes(this.q.toLowerCase())) return false;
        }
        return true;
      });
      const ref = this.nearId && all.find((x) => x.id === this.nearId);
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
      return items;
    },
    count() {
      return (this._results || []).length;
    },
  }));

  // Compare: two planets side by side, over the same fetched index. Shows the colour-driving
  // data (temperature, host star, atmosphere, size) plus fun facts (distance, discovery).
  Alpine.data("compare", (cfg) => ({
    indexUrl: (cfg && cfg.indexUrl) || null,
    loaded: false,
    all: [],
    byId: {},
    aId: null, bId: null,
    // Planet-browser state (the pop-over used to pick a planet for a slot).
    pickerOpen: false, pickerSlot: null, pq: "", pfam: null, ptypeF: "all",
    familyMetaC: {
      teal: { n: "Teal", c: "#2fb8b8" }, azure: { n: "Azure", c: "#3ea5ff" },
      blue: { n: "Blue", c: "#4a7fd0" }, periwinkle: { n: "Periwinkle", c: "#aab6e6" },
      green: { n: "Green", c: "#4caf6a" }, gold: { n: "Gold", c: "#d9b44a" },
      orange: { n: "Orange", c: "#e08a3c" }, red: { n: "Red", c: "#d0503c" },
      pink: { n: "Pink", c: "#d06a9c" }, violet: { n: "Violet", c: "#9a7fd0" },
      brown: { n: "Brown", c: "#8a6a4a" }, grey: { n: "Grey", c: "#9aa0ac" },
      white: { n: "White", c: "#dfe3ea" }, dark: { n: "Dark", c: "#3a3f4a" },
    },
    familyOrderC: ["teal", "azure", "blue", "periwinkle", "green", "gold", "orange", "red", "pink", "violet", "brown", "grey", "white", "dark"],
    async init() {
      try {
        const res = await fetch(this.indexUrl);
        this.all = await res.json();
        this.all.forEach((p) => { this.byId[p.id] = p; });
      } catch (e) { /* leave empty */ }
      const u = new URLSearchParams(location.search);
      this.aId = u.get("a"); this.bId = u.get("b");
      this.loaded = true;
      this.$watch("aId", () => this._render());
      this.$watch("bId", () => this._render());
      this.$nextTick(() => this._render());
    },
    a() { return this.byId[this.aId] || null; },
    b() { return this.byId[this.bId] || null; },
    // --- planet browser ---
    openPicker(slot) {
      this.pickerSlot = slot; this.pq = ""; this.pfam = null; this.ptypeF = "all";
      this.pickerOpen = true;
      this.$nextTick(() => this.$refs.pickerSearch && this.$refs.pickerSearch.focus());
    },
    closePicker() { this.pickerOpen = false; },
    choose(id) {
      if (this.pickerSlot === "a") this.aId = id; else this.bId = id;
      this.closePicker();
    },
    pickerFamilies() {
      const present = new Set(this.all.map((p) => p.family));
      return this.familyOrderC.filter((f) => present.has(f))
        .map((f) => ({ id: f, name: this.familyMetaC[f].n, colour: this.familyMetaC[f].c }));
    },
    pickerTypes() {
      const present = new Set(this.all.map((p) => p.ptype));
      const order = ["rocky", "super-earth", "neptune", "gas-giant", "hot-jupiter"];
      return [["all", "All"], ...order.filter((t) => present.has(t))
        .map((t) => [t, this.typeLabelsC[t]])];
    },
    pickerResults() {
      const q = this.pq.toLowerCase().trim();
      return this.all.filter((p) => {
        if (this.pfam && p.family !== this.pfam) return false;
        if (this.ptypeF !== "all" && p.ptype !== this.ptypeF) return false;
        if (q && !((p.name + " " + p.host).toLowerCase().includes(q))) return false;
        return true;
      }).sort((x, y) => x.name.localeCompare(y.name));
    },
    fmtLy(p) { return p.dist_ly != null ? p.dist_ly.toLocaleString() + " ly" : "distance n/a"; },
    swap() { [this.aId, this.bId] = [this.bId, this.aId]; },
    _render() {
      const u = new URLSearchParams();
      if (this.aId) u.set("a", this.aId);
      if (this.bId) u.set("b", this.bId);
      history.replaceState(null, "", u.toString() ? "?" + u.toString() : location.pathname);
      this.$nextTick(() => {
        [["cA", this.a()], ["cB", this.b()]].forEach(([ref, p]) => {
          const cv = this.$refs[ref];
          if (!cv || !p || !window.PlanetRender) return;
          window.PlanetRender.render(cv, {
            palette: p.palette, radius: p.radius, cloudState: p.cloud, lumY: p.lum,
            style: "retro", fidelity: localStorage.getItem("renderFidelity") || "classic",
          });
        });
      });
    },
    // --- formatting ---
    _n(v, unit, dp) {
      if (v == null) return "n/a";
      const num = dp != null ? (+v).toFixed(dp) : (+v).toLocaleString();
      return num + (unit || "");
    },
    _star(p) {
      const t = p.starTeff != null ? Math.round(p.starTeff) + " K" : "";
      return [t, p.starType].filter(Boolean).join(" · ") || "n/a";
    },
    _size(p) {
      const r = p.radius != null ? (+p.radius).toFixed(1) + " R⊕" : null;
      let m = null;
      if (p.mass != null) {
        const mv = +p.mass;
        m = (mv >= 100 ? Math.round(mv).toLocaleString() : mv.toFixed(1)) + " M⊕";
      }
      return [r, m].filter(Boolean).join(" · ") || "n/a";
    },
    _disc(p) { return [p.disc, p.year].filter(Boolean).join(" · ") || "n/a"; },
    _typeLabel(t) { return (this.typeLabelsC && this.typeLabelsC[t]) || t || "n/a"; },
    typeLabelsC: {
      rocky: "Rocky", "super-earth": "Super-Earth", neptune: "Neptune-like",
      "gas-giant": "Gas giant", "hot-jupiter": "Hot Jupiter", unknown: "Unknown",
    },
    // The comparison table, grouped. `diff` flags rows where the two differ, for highlighting.
    groups() {
      const A = this.a(), B = this.b();
      if (!A || !B) return [];
      const row = (label, fa, fb) => ({ label, a: fa, b: fb });
      return [
        { title: "What drives the colour", rows: [
          row("Colour", A.hex, B.hex),
          row("Equilibrium temp", this._n(A.temp, " K", 0), this._n(B.temp, " K", 0)),
          row("Host star", this._star(A), this._star(B)),
          row("Atmosphere", A.cloud, B.cloud),
          row("Metallicity", this._n(A.metal, "× solar", 1), this._n(B.metal, "× solar", 1)),
        ] },
        { title: "The planets", rows: [
          row("Type", this._typeLabel(A.ptype), this._typeLabel(B.ptype)),
          row("Size", this._size(A), this._size(B)),
          row("Distance from Earth", this._n(A.dist_ly, " ly"), this._n(B.dist_ly, " ly")),
          row("Orbit (semi-major axis)", this._n(A.sma, " AU", 2), this._n(B.sma, " AU", 2)),
          row("Discovery", this._disc(A), this._disc(B)),
        ] },
      ];
    },
    // One plain-English line on the dominant reason their colours differ.
    whyDiffer() {
      const A = this.a(), B = this.b();
      if (!A || !B) return "";
      if (A.hex === B.hex) return "These two come out <strong>almost the same colour</strong> — similar temperature, star and atmosphere give a similar reflected-light spectrum.";
      const hotter = (A.temp || 0) >= (B.temp || 0) ? A : B;
      const cooler = hotter === A ? B : A;
      const parts = [];
      if ((hotter.temp || 0) - (cooler.temp || 0) > 300) {
        parts.push(`<strong>${hotter.name}</strong> is much hotter (${Math.round(hotter.temp)} K vs ${Math.round(cooler.temp)} K), so sodium absorption drives it bluer and darker, while <strong>${cooler.name}</strong> is cool enough for brighter clouds`);
      }
      if (Math.abs((A.starTeff || 0) - (B.starTeff || 0)) > 1200) {
        const redder = (A.starTeff || 9999) <= (B.starTeff || 9999) ? A : B;
        parts.push(`their host stars differ a lot in temperature, so <strong>${redder.name}</strong> reflects a warmer, redder light`);
      }
      if (!parts.length) {
        if (A.cloud !== B.cloud) {
          parts.push(`the main difference is their atmospheres (${A.cloud} vs ${B.cloud})`);
        } else {
          return "These two are very similar worlds — close in temperature, host star and atmosphere — so their reflected-light colours come out nearly the same.";
        }
      }
      return parts.join("; ") + ".";
    },
  }));

  // Detail: full-spectrum <-> Roman toggle + palette export. Neither view is "true colour":
  // both are modelled. `init` carries the precomputed colours/palettes.
  Alpine.data("detail", (init) => ({
    view: "full",
    indexUrl: null,   // planet index URL for the RANDOM roll (injected by the page template)
    // Render fidelity: "classic" (physics-honest) or "stylised" (restyled for looks). Global, persisted.
    fidelity: localStorage.getItem("renderFidelity") || "classic",
    heroStyle: "retro",   // hero render: "retro" (pixel) or "smooth" (sphere)
    heroSource: "model",  // hero shows the "model" render or the real "telescope" image
    // Illuminant swap ("Light source" knob): "native" = the planet's own star, "sun" = the
    // same albedo re-lit by the Sun. Data injected by init when the record carries it.
    illum: "native",
    hasSun: false,
    sunHex: null, sunLum: 0, sunOog: false, sunPalette: null, sunDe: null,
    obs: [],              // real telescope images for this planet (0+), injected by init
    obsIdx: 0,            // which telescope image is selected (when >1 exist)
    phases: [],           // phase-resolved colours ({d, h, l} at 0-180°), injected by init
    phaseSource: "",      // where the phase behaviour comes from (cahoy-grid/-ratio/lambert)
    // Slider position into `phases`. Defaults to 20° — the base render's soft day/night
    // shading already depicts a slightly-off-full planet, so the label matches the picture.
    phaseIdx: 2,
    // The phase cycle: like the rotation, the hero runs a full lunar cycle — full, waning
    // to dark, then waxing back from the other side to full (0-360°, ~22 s around). On by
    // default; touching the slider pins the chosen phase, the ▶ button resumes the cycle.
    phasePlay: true,
    _anim: null,          // { deg, dir, last } — continuous animation state
    _PHASE_SPEED: 16,     // degrees per second (~10.6 s per sweep)
    obsZoom: false,       // real-image lightbox open?
    msg: "",
    help: false,       // dossier "how to read this" expandable (ℹ button)
    info: null,        // which scope explainer is open: 'view' | 'style' | 'source' | null
    panel: "palette",  // mobile-only: which info panel shows ('readout' | 'palette' | 'data')
    descOpen: false,   // mobile-only: caption under the planet name expanded?
    ledFlash: false,   // channel LED blink on view change
    sweep: false,      // CRT redraw sweep on view change
    _t: null,
    _lt: null,
    _st: null,
    ...init,
    // Carry the scope's settings across same-system hops (each planet is its own page).
    // Every option falls back gracefully when the target planet can't honour it.
    init() {
      const v = localStorage.getItem("scopeView");
      if (v === "full" || v === "roman") this.view = v;
      // The Light-source knob position also survives hops — but only onto planets that
      // carry a Sun-swap (all should; the guard keeps a missing one from wedging the UI).
      const il = localStorage.getItem("scopeIllum");
      if (il === "sun" && this.hasSun) this.illum = "sun";
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
      window.__randomGo = () => this.randomGo();  // wire the R shortcut to this page
      this._phaseLoop();  // start the wax/wane phase cycle (on by default)
    },
    // Jump to a random planet. The detail page doesn't carry the index, so fetch it lazily
    // on the first roll (cached in window.PLANETS for every roll after).
    async randomGo() {
      if (!window.PLANETS || !window.PLANETS.length) {
        if (!this.indexUrl) return;
        try {
          const res = await fetch(this.indexUrl);
          window.PLANETS = await res.json();
        } catch (e) { return; }
      }
      ExoRandom.go(window.PLANETS);
    },
    _persist(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
    blink() {
      this.ledFlash = true;
      clearTimeout(this._lt);
      this._lt = setTimeout(() => (this.ledFlash = false), 320);
    },
    // Scope controls: every knob/button drives real state (and persists across hops):
    setView(v) { this.view = v; this._persist("scopeView", v); this.blink(); this._sweep(); },
    // Restart the CRT sweep animation (drop the class for a frame so CSS re-triggers it).
    _sweep() {
      this.sweep = false;
      requestAnimationFrame(() => {
        this.sweep = true;
        clearTimeout(this._st);
        this._st = setTimeout(() => (this.sweep = false), 550);
      });
    },
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
    // --- Illuminant swap ("Light source" knob) ------------------------------------------
    // True when the Sun-lit variant is what's on screen (full-spectrum channel only: the
    // Roman 4-band channel has no Sun-swap, so on CH2 the native data always shows).
    sunSet() { return this.hasSun && this.illum === "sun"; },      // the knob's position
    sunlit() { return this.sunSet() && this.view === "full"; },    // ...and it's on screen
    // The active channel's palette/colour/etc — one source of truth for the hero render,
    // the readouts, the dossier and the palette exports.
    curPalette() { return this.view === "roman" ? this.romanPalette : (this.sunlit() ? this.sunPalette : this.fullPalette); },
    curHex() { return this.view === "roman" ? this.romanHex : (this.sunlit() ? this.sunHex : this.fullHex); },
    curLum() { return this.view === "roman" ? this.romanLum : (this.sunlit() ? this.sunLum : this.fullLum); },
    curOog() { return this.view === "roman" ? this.romanOog : (this.sunlit() ? this.sunOog : this.fullOog); },
    // What the palette-out / dossier headers call the current output.
    viewName() {
      if (this.view === "roman") return "Roman 4-band";
      return this.sunlit() ? "full spectrum · Sun-lit" : "full spectrum";
    },
    // Flip the lamp. On the Roman channel the knob isn't locked out: the first click brings
    // back the full-spectrum channel (where the swap lives), a further click then flips it —
    // the same forgiving pattern as the Style knob while the telescope photo is showing.
    toggleIlluminant() {
      if (!this.hasSun) return;
      if (this.view === "roman") { this.setView("full"); return; }
      this.illum = this.illum === "native" ? "sun" : "native";
      this._persist("scopeIllum", this.illum);
      this.blink();
      this._sweep();
    },
    // Phase slider: the current stop, a plain-English name for it, and the redraw hook.
    phase() { return this.phases[this.phaseIdx] || { d: 0, h: this.fullHex, l: this.fullLum }; },
    phaseName() {
      const d = this.phase().d;
      if (d === 0) return "fully lit";
      if (d < 90) return "gibbous";
      if (d === 90) return "half lit";
      if (d < 180) return "crescent";
      return "new (backlit)";
    },
    phaseChanged() {
      // A manual phase pick pins it (pauses the cycle); sliding while the real photo shows
      // brings the model back (photos have their own phase).
      this._pinPhase();
      if (this.heroSource === "telescope") { this.heroSource = "model"; this._persist("heroSource", "model"); }
      this.renderAll();
    },
    _phaseLoop() { this.renderAll(); },  // (re)issue the spin with/without the animator
    togglePhasePlay() {
      this.phasePlay = !this.phasePlay;
      this._anim = null;  // restart the sweep from the current slider phase
      this.renderAll();
    },
    _pinPhase() {
      if (!this.phasePlay) return;
      this.phasePlay = false;
      this._anim = null;
    },
    // Per-frame animator handed to the spin loop: a full lunar cycle. The light orbits
    // 0-360°: full -> waning (shadow closes in from the left) -> a brief dark moment ->
    // waxing (light returns on the LEFT and grows) -> full again. The slider/readout track
    // the effective illumination (0-170°, side-agnostic) at the nearest 10° stop.
    _phaseFrame(t) {
      if (this.heroSource === "telescope") return null;
      if (!this._anim) this._anim = { deg: this.phase().d, last: t };
      const a = this._anim;
      a.deg += this._PHASE_SPEED * (Math.min(t - a.last, 100) / 1000);
      a.last = t;
      if (a.deg >= 360) a.deg -= 360;
      const eff = a.deg <= 180 ? a.deg : 360 - a.deg;  // illumination phase, side-agnostic
      const idx = Math.max(0, Math.min(this.phases.length - 2, Math.round(eff / 10)));
      if (idx !== this.phaseIdx) this.phaseIdx = idx;
      return {
        phase: (a.deg * Math.PI) / 180,
        palette: this._phaseTint(this.curPalette(), idx),
      };
    },
    // Retint a palette by the per-channel drift of the phase colour vs full phase, so the
    // render carries the modelled colour shift (subtle blueing/reddening) as it wanes.
    _phaseTint(palette, idx) {
      const ph = this.phases[idx == null ? this.phaseIdx : idx];
      if (!ph || !ph.d || !this.phases.length) return palette;
      const base = this.phases[0].h;
      const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
      const [br, bg, bb] = rgb(base), [pr, pg, pb] = rgb(ph.h);
      const ratio = [pr / (br || 1), pg / (bg || 1), pb / (bb || 1)];
      return palette.map((hex) => {
        const c = rgb(hex).map((v, i) => Math.max(0, Math.min(255, Math.round(v * ratio[i]))));
        return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
      });
    },
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
      const pal = this.curPalette();
      navigator.clipboard?.writeText(pal.join(", "));
      this.flash("copied all " + pal.length + " colours");
    },
    copyCssVars() {
      const pal = this.curPalette();
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
        palette: this._phaseTint(this.curPalette()),
        radius: this.radius,
        cloudState: this.cloudState,
        lumY: this.curLum(),
        fidelity: this.fidelity,
        phase: (this.phase().d * Math.PI) / 180,
      };
      // Single hero planet, rotating; its style (sphere/pixel) is a scope knob. When the
      // phase cycle is playing, the animator supplies a smoothly-advancing phase per frame.
      this.$refs.cHero.classList.toggle("pixel", this.heroStyle === "retro");
      const frame = this.phasePlay && this.phases.length > 1 ? (t) => this._phaseFrame(t) : null;
      PlanetRender.spin(this.$refs.cHero, { ...opts, style: this.heroStyle, frame: frame });
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
          phase: window.PlanetRender.hashPhase(pl.id),
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
// and keeps the site light: only the hovered planet animates). The hovered planet also
// runs the same full lunar cycle as the planet page — waning through dark, waxing back
// from the left — picking up from the card's dealt phase. Un-hovering restores it.
(function () {
  if (!window.matchMedia || !window.matchMedia("(hover: hover)").matches) return;
  var PHASE_SPEED = 16;  // degrees per second, matching the planet page's cycle
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
      phase: window.PlanetRender.hashPhase(p.id),
    };
  }
  // Per-hover animator: advances the phase through the full 0-360° cycle from `startRad`.
  function phaseAnimator(startRad) {
    var deg = (startRad * 180) / Math.PI, last = null;
    return function (t) {
      if (last == null) last = t;
      deg += (PHASE_SPEED * Math.min(t - last, 100)) / 1000;
      last = t;
      if (deg >= 360) deg -= 360;
      return { phase: (deg * Math.PI) / 180 };
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
      if (o) window.PlanetRender.spin(cv, Object.assign({}, o, { frame: phaseAnimator(o.phase) }));
    }
  });
})();
