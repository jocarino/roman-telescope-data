// Alpine components + the gallery hold-to-peek. No build step; plain ES.

// One reusable collator for name sorting. `String.localeCompare` builds its collation rules on
// every call, which is thousands of times over a catalogue this size; a hoisted Intl.Collator
// does that work once. Same ordering, just not rebuilt per comparison.
const NAME_COLLATOR = new Intl.Collator();

// Everything a search query and a planet name are allowed to disagree about: spaces, hyphens,
// dots, plus signs. Stripped from both sides so "trappist 1" finds TRAPPIST-1.
const NON_ALNUM = /[^a-z0-9]+/g;

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

// Shared sky maths for the "your horizon" overlay and the /sky.html "your sky tonight"
// page. All angles in degrees; `lon` is the exact longitude if geolocation was granted,
// or null to estimate it from the clock's UTC offset (15°/hour — up to an hour of sky
// off under daylight saving).
window.ExoSky = {
  // Local sidereal time: which RA is crossing the observer's meridian right now.
  // Low-precision GMST, minutes-accurate for decades around J2000.
  lstDeg(lon) {
    const d = (Date.now() - Date.UTC(2000, 0, 1, 12)) / 86400000;
    const lonDeg = lon != null ? lon : (-new Date().getTimezoneOffset() / 60) * 15;
    return ((280.46061837 + 360.98564736629 * d + lonDeg) % 360 + 360) % 360;
  },
  // Altitude above the horizon + azimuth (0°=N, 90°=E) of a sky position, right now.
  altAzDeg(raDeg, decDeg, latDeg, lon) {
    const r = Math.PI / 180, phi = latDeg * r, dec = decDeg * r;
    const H = (this.lstDeg(lon) - raDeg) * r;
    const sa = Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H);
    const alt = Math.asin(Math.max(-1, Math.min(1, sa))) / r;
    const az = Math.atan2(-Math.cos(dec) * Math.sin(H),
      Math.sin(dec) * Math.cos(phi) - Math.cos(dec) * Math.sin(phi) * Math.cos(H)) / r;
    return { alt: alt, az: (az + 360) % 360 };
  },
  compass(azDeg) {
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][Math.round(azDeg / 45) % 8];
  },
  // Declination of the observer's horizon at a given RA: tan(dec) = -cos(H) / tan(lat).
  horizonDec(latDeg, lstDeg, raDeg) {
    const r = Math.PI / 180;
    return Math.atan(-Math.cos((lstDeg - raDeg) * r) / Math.tan(latDeg * r)) / r;
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

// The five solar-system anchors' real spacecraft maps, injected by the gallery template
// (web/textures.py). Every other planet gets null and renders schematic bands, because for
// every other planet a map would be invention. On by default: where ground truth exists,
// showing it is the honest thing — the colour is still the computed one either way.
window.exoMap = function (id) {
  var t = window.SURFACE_MAPS;
  return (t && t[id]) || null;
};

// The phase a card is drawn at. Cards normally take the full 10-140 deg spread, which is what
// gives the grid its variety — but a real map is the entire point of the five that have one,
// and past ~55 deg the crescent has eaten the geography: Earth becomes a sliver of ocean with
// no continent on it. So a mapped card is dealt from the lit end of the same range. Hovering
// still runs the whole wax/wane cycle; this is only where it rests.
window.exoCardPhase = function (id) {
  var ph = window.PlanetRender.hashPhase(id);
  return window.exoMap(id) ? Math.min(ph, 0.96) : ph;   // 0.96 rad ~ 55 deg
};

// How wide this planet's card frame is, relative to its height. A ringed planet renders wide
// and overflows its card (see .card-planet.ringed) rather than shrinking its globe to ~43% to
// keep the rings inside a square: Saturn then sits the same size as every other planet in the
// grid, with its rings reaching across the gutters. 1 for everyone else.
window.exoCardAspect = function (id) {
  var m = window.exoMap(id);
  return m && m.ring ? window.PlanetRender.ringAspect(m.ring) : 1;
};

document.addEventListener("alpine:init", () => {

  // Gallery: search / filter / sort over a fetched index (window.PLANETS). Cards are rendered
  // incrementally in JS and their planet is drawn only when scrolled into view, so the grid
  // scales to thousands of planets without a heavy server-rendered DOM or an inlined index.
  // The build does inline a small boot slice (window.PLANETS_BOOT) so first paint doesn't
  // wait on the full index download; init() swaps in the real index when it arrives.
  Alpine.data("gallery", (cfg) => ({
    indexUrl: (cfg && cfg.indexUrl) || null,
    loaded: false,        // the FULL index has arrived: counts and dropdowns are trustworthy
    ready: false,         // enough planets to paint cards (the inlined boot slice counts)
    _results: null,       // cached ordered+filtered array for the current render pass
    _shown: 0,            // how many cards appended to the grid so far
    _batch: 60,           // cards appended per scroll step
    _map: null,           // id -> planet lookup
    _loadIO: null,        // appends the next batch as the sentinel nears the viewport
    _drawIO: null,        // draws each card's planet as it nears the viewport
    _qT: 0,               // pending debounce timer for the search box
    q: "",
    obs: "all",       // "how real": what light of this planet anyone has caught — see obsLabels
    roman: "all",     // on Roman's coronagraph shortlist — see romanLabels
    ptype: "all",
    disc: "all",
    distBand: "all",
    hz: "all",        // habitable-zone lens: see hzLabels
    fic: false,       // "seen in fiction" toggle: show only planets in the pop-culture overlay
    sort: "curated",  // the gallery's default order — see sortLabels and _filterDefaults
    // Which colour the whole gallery is keyed to: "full" (the modelled full spectrum) or
    // "roman" (what the Coronagraph's four bands would recover). Every colour-derived control
    // re-keys to it: the swatch, the colour-family chips, the brightness sort, the
    // similar-colour sort. Defaults OFF and is session-only — never restored from storage and
    // deliberately NOT wired to the planet pages' `scopeView`, so the catalogue you come back
    // to is the one you left. Only ?view=roman can start it on.
    view: "full",
    famCleared: "",   // family auto-dropped by a view flip (its name), for the toolbar note
    _fcT: null,
    scrolled: false,  // page scrolled past the header: toolbar is stuck, TOP button shows
    // Labels for the custom (retro) dropdowns.
    // "How real" — the observation tiers computed in web/build.py (_observation_tier). Ordered
    // most-evidence-first, which is also how the menu reads top to bottom. Each carries a
    // plain-English second line: "Photographed" alone would let a visitor assume the swatch is
    // the photo, and it never is — those images are infrared and false-coloured.
    obsLabels: {
      all: "All",
      colour: "Its colour, measured",
      photo: "Photographed",
      // Kept short enough that the label and its count stay on one line in the menu's width:
      // "Seen directly, no image · 71" wrapped, and a count orphaned on its own line reads
      // like a second option rather than part of this one.
      imaged: "Seen directly",
      unseen: "Never seen",
      lost: "Never seen again",
    },
    obsSubs: {
      all: "",
      colour: "visible spectrum, solar system",
      photo: "coronagraph image, infrared",
      imaged: "imaging discovery, no picture here",
      unseen: "inferred from its star's light",
      lost: "microlensing — a one-off event",
    },
    // Roman's coronagraph shortlist. Its own filter, NOT a "how real" tier: being a target
    // says where the telescope can point, nothing whatsoever about how the colour was derived.
    romanLabels: { all: "Any", yes: "On Roman's list" },
    typeLabels: {
      all: "All types", rocky: "Rocky", "super-earth": "Super-Earth",
      neptune: "Neptune-like", "gas-giant": "Gas giant", "hot-jupiter": "Hot Jupiter",
      unknown: "Unknown",
    },
    // Habitable-zone lens. "water" is the headline case — the orbit is in the zone AND the
    // planet is small enough to have a surface. The others split the rest honestly rather
    // than hiding it: a giant at the right distance is a real, different answer.
    hzLabels: {
      all: "All planets",
      water: "Could hold liquid water",
      zone: "Right distance, no surface",
      "too-hot": "Too close to its star",
      "too-cold": "Too far from its star",
      unknown: "Not computable",
    },
    hzOrder: ["water", "zone", "too-hot", "too-cold", "unknown"],
    // Distance bands (light-years). id -> [label, maxExclusive in ly]; last band catches the rest.
    distBands: [
      ["all", "Any distance", Infinity],
      ["near", "≤ 50 ly", 50],
      ["mid", "50–300 ly", 300],
      ["far", "300–1,500 ly", 1500],
      ["remote", "> 1,500 ly", Infinity],
    ],
    // "curated" is the default and deliberately first: alphabetical opens the catalogue on a
    // wall of near-identical cream giants, which is the least representative thing here. The
    // curated order (pipeline/curate.py, shipped as each planet's "c") opens on the five
    // solar-system worlds we can check against real measurements, then deals one card of every
    // colour family in turn. Name is still here, one click away, for looking something up.
    sortLabels: {
      curated: "Sort: curated", name: "Sort: name", temp: "Sort: hottest",
      lum: "Sort: brightest", dist: "Sort: nearest Earth", de: "Sort: colour lost to Roman",
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
    // Which sections of the filter/sort menu are open. All shut by default — expanded, the
    // menu is a wall of options you have to scroll past to reach anything — and the set the
    // user opens is remembered across visits, like the accent/style/fidelity prefs.
    // Stored as the list of OPEN keys rather than shut ones, so a section added in a later
    // release starts collapsed too instead of inheriting someone's old storage.
    openSec: (() => {
      const o = {};
      try {
        const saved = JSON.parse(localStorage.getItem("menuSections") || "[]");
        if (Array.isArray(saved)) saved.forEach((k) => { o[k] = true; });
      } catch (e) { /* ignore */ }
      return o;
    })(),
    secOpen(k) { return !!this.openSec[k]; },
    // Whether a section holds a non-default choice. Collapsed sections would otherwise hide
    // an active filter completely, so the heading carries the same small accent dot the
    // hamburger button itself uses. Kept in step with that button's `active` condition.
    secActive(k) {
      if (k === "obs") return this.obs !== "all";
      if (k === "roman") return this.roman !== "all";
      if (k === "ptype") return this.ptype !== "all";
      if (k === "hz") return this.hz !== "all";
      if (k === "dist") return this.distBand !== "all";
      if (k === "disc") return this.disc !== "all";
      if (k === "sort") return this.sort !== this._filterDefaults.sort;
      return false;  // render + accent are display prefs, not filters: no value is "set"
    },
    toggleSec(k) {
      this.openSec[k] = !this.openSec[k];
      try {
        localStorage.setItem("menuSections",
          JSON.stringify(Object.keys(this.openSec).filter((s) => this.openSec[s])));
      } catch (e) { /* ignore */ }
    },
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
    // Flipping the view changes what every swatch IS, so a colour family selected in one view
    // can have no members in the other — Roman's bluest band is 575 nm and nothing below it is
    // sampled, so azure empties out completely. Drop the filter and say why, rather than
    // leaving the visitor staring at an empty grid wondering what broke.
    toggleView() { this.setView(this.view === "roman" ? "full" : "roman"); },
    // The hold-to-peek loader and the hover-to-spin animator live outside this component and
    // still have to draw the colour that is on screen. They read this, not localStorage —
    // the view is session state now, so there is nothing stored for them to read.
    _publishView() { window.__exoView = this.view; },
    setView(v) {
      if (v === this.view) return;
      this.view = v;
      this._publishView();
      clearTimeout(this._fcT);
      if (this.family && !this.families().some((f) => f.id === this.family)) {
        this.famCleared = this.familyMeta[this.family].n;
        this.family = null;
        this._fcT = setTimeout(() => (this.famCleared = ""), 7000);
      } else {
        this.famCleared = "";
      }
    },
    // The colour this planet wears in the current view. The `r*` fields are written by the
    // build; fall back to the full-spectrum colour if an entry predates them (a cached boot
    // slice from an older build) so a card is never blank.
    hexOf(p) { return this.view === "roman" && p.rhex ? p.rhex : p.hex; },
    // Derived from the base hex, not carried in the index: the ramp is a pure function of it
    // (PlanetRender.ramp, matching pipeline/palette/derive.py exactly), and shipping ten more
    // hexes per planet was ~29% of the index for something every client can recompute.
    palOf(p) { return window.PlanetRender.ramp(this.hexOf(p)); },
    famOf(p) { return this.view === "roman" && p.rfam ? p.rfam : p.family; },
    // The words the UI itself puts on screen — the colour-family chips and the planet-type
    // labels — found nothing, because the box only ever read names: "blue" and "hot jupiter"
    // both came back empty while the menu right above listed 925 and 767 of them. Returns a
    // predicate for the term, or null if the query isn't one of our own words.
    _vocabMatch(qn) {
      if (this.familyMeta[qn]) return (p) => this.famOf(p) === qn;
      const type = Object.keys(this.typeLabels).find((t) => t !== "all" && (
        t.replace(NON_ALNUM, "") === qn ||
        this.typeLabels[t].toLowerCase().replace(NON_ALNUM, "") === qn));
      return type ? (p) => p.ptype === type : null;
    },
    lumOf(p) { return this.view === "roman" && p.rlum != null ? p.rlum : p.lum; },
    // Paint the inlined boot slice immediately, fetch the full index in the background, and
    // honour /?near= and /?family= deep links.
    // ---- Filter permanence ----
    // Where you are in a 5,764-planet catalogue is worth keeping: open a planet, come back
    // (browser Back, or ALL PLANETS, which is a plain link to "/") and the grid is as you
    // left it. Only non-default values are written, so clearing everything removes the entry
    // rather than leaving a fossil behind.
    _filterKeys: ["q", "obs", "roman", "ptype", "disc", "distBand", "hz", "family", "fic", "sort",
      "nearId"],
    _filterDefaults: {
      q: "", obs: "all", roman: "all", ptype: "all", disc: "all", distBand: "all", hz: "all",
      family: null, fic: false, sort: "curated", nearId: null,
    },
    filtersDirty() {
      return this._filterKeys.some((k) => this[k] !== this._filterDefaults[k]);
    },
    clearFilters() {
      this._filterKeys.forEach((k) => { this[k] = this._filterDefaults[k]; });
    },
    // One chip per non-default filter, under the toolbar. Filters outlive the visit, so a
    // returning visitor can meet a catalogue that was quietly cut down weeks ago — the menu
    // rows read the same shut whether they hold a choice or not, and the count says "925
    // shown" with nothing to compare it against. The chips say what is on and take it off
    // again in one tap. Order matches the menu, so the row reads like the menu you'd open.
    activeFilters() {
      const out = [];
      const add = (k, label, dot) => out.push({ k, label, dot: dot || "" });
      if (this.q) add("q", "“" + this.q + "”");
      if (this.family) add("family", this.familyMeta[this.family].n, this.familyMeta[this.family].c);
      if (this.fic) add("fic", "Seen in fiction");
      if (this.obs !== "all") add("obs", this.obsLabels[this.obs]);
      if (this.roman !== "all") add("roman", this.romanLabels[this.roman]);
      if (this.ptype !== "all") add("ptype", this.typeLabels[this.ptype]);
      if (this.hz !== "all") add("hz", this.hzLabels[this.hz]);
      if (this.distBand !== "all") {
        const band = this.distBands.find(([id]) => id === this.distBand);
        add("distBand", band ? band[1] : this.distBand);
      }
      if (this.disc !== "all") add("disc", this.disc);
      if (this.nearId) add("nearId", "Nearest in colour to " + (this.nearName() || "…"), this.nearHex());
      // Sort is not a filter — it hides nothing — but a remembered one silently replaces the
      // curated front page, which is the whole reason this row exists. Last, and it says so.
      if (this.sort !== this._filterDefaults.sort) add("sort", this.sortLabels[this.sort]);
      return out;
    },
    dropFilter(k) { this[k] = this._filterDefaults[k]; },
    // A search term is a question you asked once, not a setting: restored a week later it is
    // indistinguishable from a broken site (a stale typo lands you on "No planets match these
    // filters" as your front door). Every other filter is a choice worth keeping — this one
    // lives and dies with the visit.
    _sessionOnly: ["q"],
    _saveFilters() {
      const out = {};
      this._filterKeys.forEach((k) => {
        if (this._sessionOnly.includes(k)) return;
        if (this[k] !== this._filterDefaults[k]) out[k] = this[k];
      });
      try {
        if (Object.keys(out).length) localStorage.setItem("galleryFilters", JSON.stringify(out));
        else localStorage.removeItem("galleryFilters");
      } catch (e) { /* ignore */ }
    },
    // Restored BEFORE the query string is read, so an explicit deep link (?family=, ?near=,
    // ?hz=, ?fiction=1) always beats whatever happened to be on screen last time.
    _restoreFilters() {
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem("galleryFilters") || "null"); }
      catch (e) { return; }
      if (!saved || typeof saved !== "object") return;
      const ok = {
        obs: (v) => v in this.obsLabels,
        roman: (v) => v in this.romanLabels,
        ptype: (v) => v in this.typeLabels,
        hz: (v) => v in this.hzLabels,
        family: (v) => v in this.familyMeta,
        sort: (v) => v in this.sortLabels,
        distBand: (v) => this.distBands.some(([id]) => id === v),
        fic: (v) => typeof v === "boolean",
        q: (v) => typeof v === "string",
        // disc holds raw discovery-method names from the index, which hasn't loaded yet, and
        // nearId is a planet id — neither can be checked here. A stale one matches nothing,
        // and the empty grid offers a reset.
        disc: (v) => typeof v === "string",
        nearId: (v) => typeof v === "string",
      };
      this._filterKeys.forEach((k) => {
        if (this._sessionOnly.includes(k)) return;   // and a blob from an older build may hold one
        if (k in saved && ok[k] && ok[k](saved[k])) this[k] = saved[k];
      });
    },
    async init() {
      const params = new URLSearchParams(location.search);
      // A URL that names a view (?near=, ?family=, ?fiction=, ?hz=) is someone asking for
      // that exact view — a shared or bookmarked link has to look the same for everybody, so
      // it starts from the defaults. Only an unqualified visit to "/" restores what you last
      // had on screen; that is the case the back button hits.
      const linked = ["near", "family", "fiction", "hz"].some((k) => params.has(k));
      if (!linked) this._restoreFilters();
      const near = params.get("near");
      if (near) this.nearId = near;
      const fam = params.get("family");
      if (fam && this.familyMeta[fam]) this.family = fam;
      if (params.get("fiction") === "1") this.fic = true;
      const hz = params.get("hz");
      if (hz && this.hzLabels[hz]) this.hz = hz;
      // The Roman view always starts OFF. It is deliberately not restored from anywhere: not
      // from the planet pages' scope (flipping one planet to 4-band must not silently repaint
      // the whole catalogue on the way back) and not from a previous session. The one way in
      // is an explicit ?view=roman link, which is somebody asking for it by name.
      const qview = params.get("view");
      if (qview === "roman") this.view = "roman";
      this._publishView();

      // Append the next batch as the sentinel nears the viewport (infinite scroll).
      this._loadIO = new IntersectionObserver((entries) => {
        if (entries.some((e) => e.isIntersecting)) this._fill();
      }, { rootMargin: "800px" });
      this._loadIO.observe(this.$refs.sentinel);

      // Draw each planet lazily, one observer entry per card. The browser tells us when a card
      // nears the viewport instead of us re-scanning the grid on every scroll frame — that old
      // pass walked every card appended so far, so scrolling got steadily more expensive the
      // deeper you went. rootMargin keeps the one-screen lead-in the scan used to have.
      this._drawIO = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) this._draw(e.target); });
      }, { rootMargin: "100% 0px" });

      // A card is painted once and then left alone, so an anchor whose map is still decoding
      // would keep its schematic bands for the rest of the visit. Start the maps downloading
      // now, and repaint just those five when one lands — never the whole grid, which on a
      // 5,700-card page would be a visible hitch for the sake of five planets.
      if (window.PlanetRender && window.SURFACE_MAPS) {
        Object.keys(window.SURFACE_MAPS).forEach((id) => {
          window.PlanetRender.preload(window.SURFACE_MAPS[id]);
        });
        window.PlanetRender.onTexture(() => this._redrawMapped());
      }

      // Any filter/sort change re-renders the grid from the top, and is remembered.
      // Typing is the exception: "q" changes on every keystroke, and a rerender re-filters and
      // re-sorts the whole catalogue, then tears the grid down and rebuilds it. Coalesce a
      // burst of typing into a single pass instead of doing that per character.
      this._filterKeys.forEach((k) => {
        if (k === "q") return;
        this.$watch(k, () => { this._saveFilters(); this._rerender(); });
      });
      this.$watch("q", () => {
        clearTimeout(this._qT);
        this._qT = setTimeout(() => { this._saveFilters(); this._rerender(); }, 140);
      });
      // The Roman view is watched separately and deliberately NOT a filter key: it is session
      // state that always starts off, so it must not be written into the remembered filter
      // blob. It still forces a full rerender — it can reorder results (brightest,
      // similar-colour) and every card's swatch is rebuilt from scratch.
      this.$watch("view", () => this._rerender());

      window.__randomGo = () => this.randomGo();  // wire the R shortcut to this gallery

      // First paint: the build inlines the head of the default (name-sorted, unfiltered) view,
      // so the first screens of cards render without waiting for the multi-MB index. Deep links
      // change the ordering/filtering, so they wait for the real thing.
      // Filters only REMOVE planets and never reorder them, and the boot slice is pre-sorted
      // with the same name rule results() uses — so a filtered boot slice is still the correct
      // prefix of the filtered results, and can paint at once. Only a re-sort invalidates it:
      // a different sort key, or the similar-colour ranking, reorders the whole catalogue, so
      // those (and only those) wait for the full index.
      const boot = window.PLANETS_BOOT;
      const reordered = this.sort !== this._filterDefaults.sort || !!this.nearId;
      if (!reordered && boot && boot.length) this._adopt(boot, false);

      try {
        const res = await fetch(this.indexUrl);
        this._adopt(await res.json(), true);
      } catch (e) { if (!this.ready) this._adopt([], true); }
    },
    // Swap in a planet list. When the full index lands after the boot slice already painted,
    // keep the cards on screen if they're still the correct prefix of the full results
    // (they are, unless the user filtered/sorted mid-download); otherwise redraw in place
    // without the scroll-to-top a user-driven rerender does.
    _adopt(planets, full) {
      window.PLANETS = planets;
      this._map = {};
      // Lowercase once here, not inside the filter and the comparator. Both run over the whole
      // catalogue on every keystroke, so doing it per row per pass was tens of thousands of
      // throwaway strings for two values that never change.
      planets.forEach((p) => {
        this._map[p.id] = p;
        p._lc = p.name.toLowerCase();
        p._q = p._lc + " " + (p.host || "").toLowerCase();
        // Separator-blind twin of _q. Catalogue names hyphenate ("TRAPPIST-1 b", "Kepler-186 f")
        // and people type a space, so "trappist 1" and "kepler 186" both found nothing at all.
        // Stripping everything but letters and digits from BOTH sides makes the separator
        // irrelevant without loosening the match in any other way.
        p._qn = p._q.replace(NON_ALNUM, "");
      });
      const first = !this.ready;
      this.ready = true;
      if (full) this.loaded = true;
      if (first) { this._rerender(); return; }
      const results = this.results();
      const samePrefix = this._results && this._shown <= results.length &&
        this._results.slice(0, this._shown).every((p, i) => p.id === results[i].id);
      this._results = results;
      if (!samePrefix) this._clearGrid();
      this._fill();
    },
    // Jump to a random planet — within the current filters (far more delightful than fully
    // random), falling back to the whole catalog when the filter matches nothing.
    randomGo() {
      if (!this.ready) return;
      ExoRandom.go(this._results && this._results.length ? this._results : window.PLANETS);
    },
    // --- Incremental grid rendering ---------------------------------------------------------
    // Drop every card. The draw observer holds a reference to each canvas it watches, so it has
    // to be disconnected rather than left pointing at detached nodes — otherwise every filter
    // change would leak another gridful. _appendBatch re-observes the cards it adds.
    _clearGrid() {
      if (this._drawIO) this._drawIO.disconnect();
      this.$refs.grid.replaceChildren();
      this._shown = 0;
    },
    _rerender() {
      if (!this.ready) return;
      window.scrollTo(0, 0);  // results changed: show them from the top, not mid-scroll
      this._results = this.results();
      this._clearGrid();
      this._fill();
    },
    // Append batches until the sentinel is pushed out of the pre-load zone (or results run out).
    _fill() {
      if (!this.ready || !this._results) return;
      if (this._shown >= this._results.length) return;
      this._appendBatch();
      requestAnimationFrame(() => {
        if (this._shown >= this._results.length) return;
        const r = this.$refs.sentinel.getBoundingClientRect();
        if (r.top < window.innerHeight + 800) this._fill();
      });
    },
    _appendBatch() {
      if (!this.ready || !this._results) return;
      const next = this._results.slice(this._shown, this._shown + this._batch);
      if (!next.length) return;
      const frag = document.createDocumentFragment();
      const fresh = [];
      next.forEach((p) => {
        const card = this._makeCard(p);
        // Query for it rather than assuming a position: a ringed planet's canvas sits inside a
        // .card-art wrapper, and taking firstChild handed the observer the wrapper — so Saturn
        // was never drawn at all.
        fresh.push(card.querySelector(".card-planet"));
        frag.appendChild(card);
      });
      this.$refs.grid.appendChild(frag);
      this._shown += next.length;
      // Observe only once the cards are actually in the document — a target handed to an
      // IntersectionObserver while it is still inside the DocumentFragment never reports back.
      if (this._drawIO) fresh.forEach((cv) => this._drawIO.observe(cv));
      this._drawNew(fresh);
    },
    // Draw one card's planet, once. A drawn card stops being observed.
    _draw(cv) {
      if (cv.dataset.drawn || !window.PlanetRender) return;
      this._drawCanvas(cv);
      cv.dataset.drawn = "1";
      if (this._drawIO) this._drawIO.unobserve(cv);
    },
    // Paint the cards of a freshly appended batch that already sit in view. The observer would
    // get to them a beat later, which is fine while scrolling but would show one frame of empty
    // cards on first paint — so the batch just added is drawn synchronously. Cost is bounded by
    // the batch size, not by how much of the catalogue is already on the page.
    _drawNew(canvases) {
      if (!window.PlanetRender) return;
      const pad = window.innerHeight;
      canvases.forEach((cv) => {
        const r = cv.getBoundingClientRect();
        if (r.bottom > -pad && r.top < window.innerHeight + pad) this._draw(cv);
      });
    },
    _makeCard(p) {
      const a = document.createElement("a");
      // .card-ringed is only for the phone layout, where the card takes the whole row —
      // see the note on .card-planet.ringed.
      a.className = "card" + (window.exoCardAspect(p.id) !== 1 ? " card-ringed" : "");
      a.href = "/planet/" + p.id;
      a.setAttribute("data-peek", "/fragments/peek/" + p.id + ".html");
      const cv = document.createElement("canvas");
      const aspect = window.exoCardAspect(p.id);
      cv.className = "card-planet" + (this.style === "retro" ? " pixel" : "")
        + (aspect !== 1 ? " ringed" : "");
      // Intrinsic size, i.e. what lays the card out before the first frame is drawn — square
      // here and a ringed card would load as a tall box and snap when the render lands.
      cv.width = Math.round(256 * aspect); cv.height = 256; cv.dataset.id = p.id;
      cv.setAttribute("aria-label", p.name + " render");
      // A ringed canvas is wider than its grid track, so it hangs inside a wrapper that holds
      // exactly the space a normal card planet would — see .card-art. Put it straight in the
      // card otherwise; there is no reason to add a box for the other 5,759 planets.
      if (aspect !== 1) {
        const art = document.createElement("span");
        art.className = "card-art";
        art.appendChild(cv);
        a.appendChild(art);
      } else {
        a.appendChild(cv);
      }
      const name = document.createElement("div");
      name.className = "card-name"; name.textContent = p.name;
      a.appendChild(name);
      const meta = document.createElement("div");
      meta.className = "card-meta";
      // At most ONE. Two marks wrap to a second line in a grid track this narrow, and a single
      // card standing a line taller drags its whole row off the baseline — which is exactly
      // the raggedness the pills caused (Earth carried three of them, Jupiter beside it two).
      // _marks is ordered rarest-first, so the survivor is always the more remarkable claim.
      const marks = this._marks(p);
      if (marks.length) meta.appendChild(marks[0]);
      a.appendChild(meta);
      return a;
    },
    // What a card says under the name — which is, for 99% of them, nothing at all.
    //
    // The grid used to hang two or three bordered pills under every planet, and they were
    // pulling the page away from the one thing it is for. "Modelled" sat on 5,755 of 5,764
    // cards: a label that appears on everything states nothing, it just draws a box. The hex
    // was a smaller, worse copy of the swatch four times its size directly above it, and it
    // still lives on the long-press peek and in full (with copy buttons) on the planet page.
    // Both are gone from the face.
    //
    // What is left is only what is genuinely RARE — about 80 cards in the whole catalogue —
    // so a mark now means "look at this one" instead of "this is a card". Each keeps its
    // words: a lone ◆ would be a costume glyph nobody can read, and the site's rule is that
    // no mark is the only signpost for what it means.
    _marks(p) {
      const out = [];
      const mark = (cls, glyph, text, title) => {
        const s = document.createElement("span");
        s.className = "card-mark" + (cls ? " " + cls : "");
        if (title) s.title = title;
        const i = document.createElement("i");
        i.textContent = glyph;
        i.setAttribute("aria-hidden", "true");
        s.appendChild(i);
        s.appendChild(document.createTextNode(text));
        out.push(s);
      };
      // Evidence, and only where there is any worth flagging. See _observation_tier in
      // web/build.py — `imaged` is deliberately not marked: it is the weakest of the claims
      // and 71 cards of quiet noise, so it stays a filter rather than becoming decoration.
      if (p.obs === "colour") {
        mark("", "◆", "measured spectrum",
          "Its real reflected-light spectrum was measured — this swatch is computed from "
          + "data, not from a model");
      } else if (p.obs === "photo") {
        mark("", "◉", "photographed",
          "A real image exists, taken with the star blocked out — in infrared and false "
          + "colour, so the picture is not this swatch");
      } else if (p.obs === "lost") {
        mark("", "⌁", "seen once",
          "Found by microlensing: a one-off brightening that will never repeat. No light "
          + "from this planet can ever be separated from its star");
      }
      // The one question every visitor arrives with, so it keeps its own colour. Only the
      // strongest case earns it: right distance AND a plausible surface.
      if (this._hzOf(p) === "water") {
        mark("water", "◉", "liquid water?",
          "Orbits in its star's habitable zone and may have a solid surface — a candidate "
          + "for liquid water, not a detection of it");
      }
      return out;
    },
    // The card badge answers one question only: was this colour computed or measured?
    // `simulated-cgi` reads "Modelled" like every other model, because that is what it is —
    // it marks a planet Roman could point at, which is a fact about the telescope's reach and
    // not about the swatch. That fact now has its own filter; it does not belong on a badge
    // whose whole job is honesty about model vs measurement.
    _provBadge(prov) {
      const m = {
        model: "Modelled", "model-microlensing": "Modelled", "simulated-cgi": "Modelled",
        "measured-cgi": "Roman: measured",
        "measured-hwo": "HWO: measured", "measured-albedo": "Spectrum: measured",
      };
      return m[prov] || prov;
    },
    _drawCanvas(cv) {
      const p = this._map[cv.dataset.id];
      if (!p || !window.PlanetRender) return;
      cv.classList.toggle("pixel", this.style === "retro");
      window.PlanetRender.render(cv, {
        palette: this.palOf(p), baseHex: this.hexOf(p), radius: p.radius, cloudState: p.cloud,
        lumY: this.lumOf(p), style: this.style, fidelity: this.fidelity,
        phase: window.exoCardPhase(p.id),
        map: window.exoMap(p.id), aspect: window.exoCardAspect(p.id),
      });
    },
    // Repaint only the cards that have a real map — see the onTexture hook in init().
    _redrawMapped() {
      if (!this.$refs.grid || !window.SURFACE_MAPS) return;
      Object.keys(window.SURFACE_MAPS).forEach((id) => {
        const cv = this.$refs.grid.querySelector('.card-planet[data-id="' + id + '"]');
        if (!cv || !cv.dataset.drawn) return;
        this._drawCanvas(cv);
      });
    },
    _redrawAll() {
      if (!this.$refs.grid) return;
      // Style/fidelity changed: every card is stale. Repaint what's on screen right away, and
      // hand the rest back to the observer so they redraw if they're scrolled to again.
      const pad = window.innerHeight;
      this.$refs.grid.querySelectorAll(".card-planet").forEach((cv) => {
        cv.removeAttribute("data-drawn");
        const r = cv.getBoundingClientRect();
        if (r.bottom > -pad && r.top < window.innerHeight + pad) this._draw(cv);
        else if (this._drawIO) this._drawIO.observe(cv);
      });
    },
    // Colour families actually present in the data, in canonical order, with a swatch + label.
    // (The `this.loaded` read makes these reactive to the async fetch populating window.PLANETS.)
    families() {
      if (!this.loaded) return [];
      const present = new Set(window.PLANETS.map((x) => this.famOf(x)));
      return this.familyOrder.filter((f) => present.has(f))
        .map((f) => ({ id: f, name: this.familyMeta[f].n, colour: this.familyMeta[f].c }));
    },
    // "How real" dropdown: "all" + only the tiers actually present, each [value, label, sub,
    // count]. The counts are load-bearing UX at this scale, not decoration — 5,680 of 5,764
    // planets are "Never seen", so picking almost any other tier collapses the grid to a
    // handful of cards, and without the number beforehand that reads as a broken filter
    // rather than as the honest shape of the catalogue.
    obsOptions() {
      if (!this.loaded) return [["all", this.obsLabels.all, "", 0]];
      const counts = {};
      // A missing `obs` is the common case, stored nowhere to keep the index small.
      window.PLANETS.forEach((x) => {
        const t = x.obs || "unseen";
        counts[t] = (counts[t] || 0) + 1;
      });
      return Object.entries(this.obsLabels)
        .filter(([v]) => v === "all" || counts[v])
        .map(([v, label]) => [v, label, this.obsSubs[v] || "", v === "all" ? 0 : counts[v]]);
    },
    // Roman shortlist: one real choice, so it only earns its row once the index confirms the
    // list joined onto planets that exist. An empty shortlist renders as "Any" alone.
    romanCount() {
      return this.loaded ? (window.PLANETS || []).filter((p) => p.rt).length : 0;
    },
    // Type dropdown options: always "all", then only the types actually present in the data.
    typeOptions() {
      if (!this.loaded) return [["all", this.typeLabels.all]];
      const present = new Set(window.PLANETS.map((x) => x.ptype));
      const order = ["rocky", "super-earth", "neptune", "gas-giant", "hot-jupiter", "unknown"];
      return [["all", this.typeLabels.all], ...order.filter((t) => present.has(t))
        .map((t) => [t, this.typeLabels[t]])];
    },
    // Which habitable-zone bucket a planet falls in. "water" needs both halves of the claim:
    // the right amount of starlight AND a plausible surface to keep an ocean on.
    _hzOf(p) {
      const inZone = p.hz === "conservative" || p.hz === "optimistic";
      if (inZone) return (p.srf === "rocky" || p.srf === "uncertain") ? "water" : "zone";
      return p.hz || "unknown";
    },
    // Habitable-zone dropdown: "all" plus every bucket present, each with its count.
    hzOptions() {
      if (!this.loaded) return [["all", this.hzLabels.all]];
      const counts = {};
      window.PLANETS.forEach((p) => {
        const b = this._hzOf(p);
        counts[b] = (counts[b] || 0) + 1;
      });
      return [["all", this.hzLabels.all], ...this.hzOrder.filter((b) => counts[b])
        .map((b) => [b, this.hzLabels[b] + " · " + counts[b].toLocaleString()])];
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
      return p ? this.hexOf(p) : "#000";
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
      const q = this._qlc = this.q ? this.q.toLowerCase() : "";  // once per pass, not per row
      const qn = q.replace(NON_ALNUM, "");
      // A name match always wins. Only when nothing in the catalogue answers to the query as a
      // NAME is it read as vocabulary, so searching "neptune" still lands on Neptune rather
      // than burying it under 1,608 Neptune-class worlds.
      let qMatch = null;
      if (qn) {
        qMatch = (p) => p._qn.includes(qn);
        if (!all.some(qMatch)) qMatch = this._vocabMatch(qn) || qMatch;
      }
      let items = all.filter((p) => {
        if (this.obs !== "all" && (p.obs || "unseen") !== this.obs) return false;
        if (this.roman !== "all" && !p.rt) return false;
        if (this.ptype !== "all" && p.ptype !== this.ptype) return false;
        if (this.disc !== "all" && p.disc !== this.disc) return false;
        if (this.distBand !== "all" && this._distBandOf(p.dist_ly) !== this.distBand) return false;
        if (this.hz !== "all" && this._hzOf(p) !== this.hz) return false;
        if (this.family && this.famOf(p) !== this.family) return false;
        if (this.fic && !p.fic) return false;
        if (qMatch && !qMatch(p)) return false;
        return true;
      });
      const ref = this.nearId && all.find((x) => x.id === this.nearId);
      if (ref) {
        // Similar-colour sort: rank by perceptual distance to the reference planet's colour.
        const rl = this._lab(this.hexOf(ref)), dc = {};
        const dist = (p) => (dc[p.id] ??= this._de(this._lab(this.hexOf(p)), rl));
        items.sort((a, b) => dist(a) - dist(b));
      } else {
        const s = this.sort;
        // Which brightness the view is keyed to is decided ONCE, not per comparison. Reading
        // it through lumOf() inside the comparator meant ~146k method calls each doing a
        // `this.view` lookup, and made the brightness sort four times slower than every other
        // sort here. Same fallback as lumOf: Roman brightness when present, else full-spectrum.
        const roman = this.view === "roman";
        const lumOf = (p) => (roman && p.rlum != null ? p.rlum : p.lum) || 0;
        items.sort((a, b) => {
          // The default order. Every ordering decision was made at build time and arrives as one
          // integer per planet (pipeline/curate.py), so this is a numeric compare and nothing
          // more — no rule to keep in step with the build. An index written before the field
          // existed has no "c" at all: those fall to the end and settle by name below.
          if (s === "curated" && (a.c != null || b.c != null)) {
            const d = (a.c ?? Infinity) - (b.c ?? Infinity);
            if (d) return d;
          }
          // Name sort is a plain lowercase code-unit compare, NOT localeCompare: the build
          // pre-sorts the inlined boot slice with the exact same rule (web/build.py), so the
          // first-paint cards are guaranteed to be the head of the full sorted list. It is also
          // where the curated sort lands if an index predates the "c" field.
          if (s === "name" || s === "curated") {
            // Compare a lowercase key cached on the row (_adopt fills it in), not
            // a.name.toLowerCase() here: a comparator runs ~73k times over this catalogue, so
            // lowercasing inside it built ~146k throwaway strings per sort. Same ordering,
            // about five times faster — which is what a mid-range phone feels while typing.
            const x = a._lc, y = b._lc;
            if (x !== y) return x < y ? -1 : 1;
            return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
          }
          if (s === "temp") return (b.temp || 0) - (a.temp || 0);
          if (s === "lum") return lumOf(b) - lumOf(a);
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

  // 404: the cockpit. Runs the hyperspace window and the RANDOM WORLD key. The window is a
  // starfield flown through at speed: stars are 3D points streaking as they pass the camera,
  // drawn into a deliberately low-res buffer and upscaled by the browser, so it pixelates the
  // same way the planet renders do. Honours prefers-reduced-motion (one static frame) and
  // stops while the tab is hidden.
  Alpine.data("cockpit", (cfg) => ({
    indexUrl: (cfg && cfg.indexUrl) || null,
    nearest: (cfg && cfg.nearest) || [],   // the 3 nearest catalog worlds (id, name, ly, ra)
    spec: (cfg && cfg.spec) || null,       // one real reflected-light curve (id, name, vals)
    warp: true,                            // the switch on the console: hyperspace <-> drift
    path: "",
    rolling: false,
    _raf: 0,
    _stars: [],

    init() {
      this.path = location.pathname + location.search || "/";
      window.__randomGo = () => this.roll();   // the site-wide R shortcut works here too
      this.$nextTick(() => this.fly());
    },
    destroy() {
      cancelAnimationFrame(this._raf);
    },

    // Jump to a random planet. Like the detail page, the index isn't on this page, so fetch
    // it on demand — the key reads "plotting a course…" while that's in flight.
    async roll() {
      if (this.rolling) return;
      if (!window.PLANETS || !window.PLANETS.length) {
        if (!this.indexUrl) return;
        this.rolling = true;
        try {
          const res = await fetch(this.indexUrl);
          window.PLANETS = await res.json();
        } catch (e) {
          this.rolling = false;
          return;
        }
      }
      ExoRandom.go(window.PLANETS);
    },

    fly() {
      const cv = this.$refs.hyper;
      if (!cv) return;
      const ctx = cv.getContext("2d");
      const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
      // One accent-tinted star in six, so the field belongs to the current palette.
      const accent = getComputedStyle(document.documentElement)
        .getPropertyValue("--accent").trim() || "#61dafb";
      const COUNT = 340, SPEED = 0.022, SPREAD = 1.9;
      const spawn = (s) => {
        s.x = (Math.random() - 0.5) * SPREAD;
        s.y = (Math.random() - 0.5) * SPREAD;
        s.z = 0.35 + Math.random() * 0.65;   // 1 = far, 0 = at the camera
        s.c = Math.random() < 0.17 ? accent : "#d3dae8";
        return s;
      };
      this._stars = Array.from({ length: COUNT }, () => spawn({}));

      let w = 0, h = 0;
      const fit = () => {
        // Fixed 1/3 scale: the chunky pixels are the point, so ignore devicePixelRatio.
        const r = cv.getBoundingClientRect();
        w = cv.width = Math.max(1, Math.round(r.width / 3));
        h = cv.height = Math.max(1, Math.round(r.height / 3));
        ctx.fillStyle = "#04060a";
        ctx.fillRect(0, 0, w, h);
      };
      fit();
      // Resizing clears the buffer. Under prefers-reduced-motion nothing is animating, so the
      // one static frame has to be redrawn or the window is left blank.
      if (window.ResizeObserver) {
        new ResizeObserver(() => { fit(); if (still) draw(false); }).observe(cv);
      }

      const draw = (step) => {
        // Fade rather than clear: each star leaves a short trail behind it.
        ctx.fillStyle = step ? "rgba(4, 6, 10, .28)" : "#04060a";
        ctx.fillRect(0, 0, w, h);
        const cx = w / 2, cy = h / 2, f = w * 0.62;
        const sp = this.warp ? SPEED : SPEED * 0.12;   // the console switch is real
        for (const s of this._stars) {
          const z0 = s.z;
          if (step) s.z -= sp;
          if (s.z <= 0.06) { spawn(s); continue; }
          const x = cx + (s.x / s.z) * f, y = cy + (s.y / s.z) * f;
          if (x < -40 || x > w + 40 || y < -40 || y > h + 40) { if (step) spawn(s); continue; }
          const near = 1 - s.z;                       // brighter and fatter as it passes
          ctx.globalAlpha = Math.min(1, 0.3 + near * 1.2);
          ctx.fillStyle = s.c;
          if (step) {
            const x0 = cx + (s.x / z0) * f, y0 = cy + (s.y / z0) * f;
            ctx.strokeStyle = s.c;
            ctx.lineWidth = near > 0.72 ? 2 : 1;
            ctx.beginPath();
            ctx.moveTo(x0, y0);
            ctx.lineTo(x, y);
            ctx.stroke();
          } else {
            ctx.fillRect(Math.round(x), Math.round(y), near > 0.72 ? 2 : 1, near > 0.72 ? 2 : 1);
          }
        }
        ctx.globalAlpha = 1;
      };

      // Dashboard instruments, drawing REAL data on green phosphor. The radar plots the
      // three nearest catalog worlds at their true sky bearings (RA as the compass angle,
      // distance rank as the ring); the trace is a real planet's reflected-light curve
      // with a slow scan cursor. Both are captioned and linked in the markup — the
      // canvases are the picture, the links are the data.
      const radar = this.$refs.radar, wave = this.$refs.wave;
      const rc = radar && radar.getContext("2d"), wc = wave && wave.getContext("2d");
      const PHOS = "#4ade80";
      const maxLy = Math.max(...this.nearest.map((p) => p.ly), 1);
      let t = 0;
      const decor = (step) => {
        if (step) t += 1;
        if (rc) {
          const W = radar.width, H = radar.height, cx = W / 2, cy = H / 2;
          rc.fillStyle = step ? "rgba(4, 10, 6, .14)" : "#040a06";   // phosphor persistence
          rc.fillRect(0, 0, W, H);
          rc.strokeStyle = "rgba(74, 222, 128, .3)";
          rc.beginPath(); rc.arc(cx, cy, W * 0.42, 0, 6.284); rc.stroke();
          rc.beginPath(); rc.arc(cx, cy, W * 0.22, 0, 6.284); rc.stroke();
          const a = t * 0.03;
          rc.strokeStyle = PHOS;
          rc.beginPath(); rc.moveTo(cx, cy);
          rc.lineTo(cx + Math.cos(a) * W * 0.42, cy + Math.sin(a) * W * 0.42); rc.stroke();
          this.nearest.forEach((p, i) => {   // real worlds: RA -> bearing, distance -> ring
            const ang = (p.ra || 0) * Math.PI / 180;
            const r = W * (0.16 + 0.26 * (p.ly / maxLy));
            const bx = cx + Math.cos(ang) * r, by = cy + Math.sin(ang) * r;
            let d = (a - ang) % 6.283; if (d < 0) d += 6.283;
            rc.globalAlpha = Math.max(0.35, 1 - d / 2.2);   // never fully dark: they're real
            rc.fillStyle = PHOS;
            rc.fillRect(Math.round(bx) - 1, Math.round(by) - 1, i === 0 ? 3 : 2, i === 0 ? 3 : 2);
            rc.globalAlpha = 1;
          });
        }
        if (wc && this.spec && this.spec.vals.length) {
          const W = wave.width, H = wave.height, vals = this.spec.vals;
          wc.fillStyle = "#040a06"; wc.fillRect(0, 0, W, H);
          wc.fillStyle = PHOS;
          for (let x = 0; x < W; x++) {   // the real albedo curve, resampled to the screen
            const v = vals[Math.min(vals.length - 1, Math.floor((x / W) * vals.length))];
            wc.fillRect(x, Math.round(2 + (1 - v) * (H - 6)), 1, 2);
          }
          if (step) {   // slow scan cursor, so the instrument reads as live
            const x = t % (W * 2) < W ? t % W : W - 1 - (t % W);
            wc.fillStyle = "rgba(74, 222, 128, .35)"; wc.fillRect(x, 0, 1, H);
          }
        }
      };

      if (still) { draw(false); decor(false); return; }
      const loop = () => {
        draw(true);
        decor(true);
        this._raf = requestAnimationFrame(loop);
      };
      loop();
      document.addEventListener("visibilitychange", () => {
        cancelAnimationFrame(this._raf);
        if (!document.hidden) loop();
      });
    },
  }));

  // Compare: two planets side by side, over the same fetched index. Shows the colour-driving
  // data (temperature, host star, atmosphere, size) plus fun facts (distance, discovery).
  Alpine.data("compare", (cfg) => ({
    indexUrl: (cfg && cfg.indexUrl) || null,
    extraUrl: (cfg && cfg.extraUrl) || null,
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
        // The star and orbit numbers this table shows live in a companion file, so the pages
        // that only need the grid don't download them. It is a parallel array in the same
        // order as the index, so the two zip by position.
        const [core, extra] = await Promise.all([
          fetch(this.indexUrl).then((r) => r.json()),
          this.extraUrl ? fetch(this.extraUrl).then((r) => r.json()).catch(() => null) : null,
        ]);
        this.all = extra && extra.length === core.length
          ? core.map((p, i) => Object.assign({}, p, extra[i]))
          : core;
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
    // The index stopped shipping a `palette` array once the ramps became client-derived, and
    // this page kept reading the field — so both strips rendered as empty outlined boxes on the
    // one page whose whole job is comparing palettes. Derive them the way the gallery does.
    pal(p) {
      return p && window.PlanetRender ? window.PlanetRender.ramp(p.hex) : [];
    },
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
      // Separator-blind, same as the gallery's box: this picker had the identical bug.
      const q = this.pq.toLowerCase().replace(NON_ALNUM, "");
      return this.all.filter((p) => {
        if (this.pfam && p.family !== this.pfam) return false;
        if (this.ptypeF !== "all" && p.ptype !== this.ptypeF) return false;
        if (q && !(p.name + " " + p.host).toLowerCase().replace(NON_ALNUM, "").includes(q)) return false;
        return true;
      }).sort((x, y) => NAME_COLLATOR.compare(x.name, y.name));
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
            palette: window.PlanetRender.ramp(p.hex), baseHex: p.hex,
            radius: p.radius, cloudState: p.cloud, lumY: p.lum,
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
    // Detection method with its glossary mark (the same mapping the planet page uses).
    _discMarked(p) {
      const term = {
        "Radial Velocity": "radial-velocity", Transit: "transit", Imaging: "direct-imaging",
        Microlensing: "microlensing",
        "Transit Timing Variations": "transit-timing-variations",
      }[p.disc];
      const marked = term ? this._gloss(term, p.disc) : p.disc;
      return [marked, p.year].filter(Boolean).join(" · ") || "n/a";
    },
    _typeLabel(t) { return (this.typeLabelsC && this.typeLabelsC[t]) || t || "n/a"; },
    typeLabelsC: {
      rocky: "Rocky", "super-earth": "Super-Earth", neptune: "Neptune-like",
      "gas-giant": "Gas giant", "hot-jupiter": "Hot Jupiter", unknown: "Unknown",
    },
    // Planet-type value with its glossary mark, for the comparison table (rendered x-html).
    _typeMarked(t) {
      const term = {
        rocky: "rocky-planet", "super-earth": "super-earth", neptune: "neptune-like",
        "gas-giant": "gas-giant", "hot-jupiter": "hot-jupiter",
      }[t];
      const label = this._typeLabel(t);
      return term && window.glossHTML ? window.glossHTML(term, label) : label;
    },
    // Jargon in a comparison row label. Falls back to the bare word if glossary.js is absent.
    _gloss(id, text) { return window.glossHTML ? window.glossHTML(id, text) : text; },
    // The comparison table, grouped. `diff` flags rows where the two differ, for highlighting.
    groups() {
      const A = this.a(), B = this.b();
      if (!A || !B) return [];
      const row = (label, fa, fb) => ({ label, a: fa, b: fb });
      // Labels and the type values carry glossary marks, so the same words explain themselves
      // here exactly as they do on a planet page. Rendered with x-html (our own strings only).
      return [
        { title: "What drives the colour", rows: [
          row("Colour", A.hex, B.hex),
          row(this._gloss("equilibrium-temperature", "Equilibrium temp"),
            this._n(A.temp, " K", 0), this._n(B.temp, " K", 0)),
          row(this._gloss("host-star", "Host star"), this._star(A), this._star(B)),
          row(this._gloss("cloud-deck", "Atmosphere"), A.cloud, B.cloud),
          row(this._gloss("metallicity", "Metallicity"),
            this._n(A.metal, "× solar", 1), this._n(B.metal, "× solar", 1)),
        ] },
        { title: "The planets", rows: [
          row("Type", this._typeMarked(A.ptype), this._typeMarked(B.ptype)),
          row("Size", this._size(A), this._size(B)),
          row(this._gloss("light-year", "Distance from Earth"),
            this._n(A.dist_ly, " ly"), this._n(B.dist_ly, " ly")),
          row(this._gloss("semi-major-axis", "Orbit (semi-major axis)"),
            this._n(A.sma, " AU", 2), this._n(B.sma, " AU", 2)),
          row("Discovery", this._discMarked(A), this._discMarked(B)),
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
        parts.push(`<strong>${hotter.name}</strong> is much hotter (${Math.round(hotter.temp)} K vs ${Math.round(cooler.temp)} K), so ${this._gloss("sodium-absorption", "sodium absorption")} drives it bluer and darker, while <strong>${cooler.name}</strong> is cool enough for brighter ${this._gloss("cloud-deck", "clouds")}`);
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
    // What the hero shows: the schematic "model" render, the same globe wearing this
    // planet's real "map" (solar-system anchors only), or the real "telescope" image.
    heroSource: "model",
    // The real spacecraft map for this planet, or null — injected by init (web/textures.py).
    map: null,
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
    // The running phase cycle (a PlanetRender.phaseCycle stepper), or null when it should
    // restart from wherever the slider now sits. Speed lives with the cycle, not here.
    _anim: null,
    obsZoom: false,       // real-image lightbox open?
    // Host star ("the lamp") swatch — injected by init; sunLampHex is the Sun's own colour,
    // for the lamp panel to follow the Light-source knob.
    starHex: null, starLabel: "", sunLampHex: null,
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
      const fromPlanet = document.referrer.includes("/planet/");
      // The Light-source knob carries only across planet-to-planet hops, never onto a page
      // you arrived at fresh or from the gallery. Every other knob is a rendering
      // preference; this one restates the physics — a sticky "sun" would silently re-light
      // a K-giant's planet by a G2 V star, and hand it a hex the gallery card never showed.
      // Same rule (and the same reason) as the telescope photo below.
      const il = localStorage.getItem("scopeIllum");
      if (il === "sun" && this.hasSun && fromPlanet) this.illum = "sun";
      // Shape shares the gallery's Sphere/Pixel key so both pages always agree.
      const hs = localStorage.getItem("planetStyle");
      if (hs === "retro" || hs === "smooth") this.heroStyle = hs;
      // Keep the same telescope selected if this planet was imaged by it too.
      const tel = localStorage.getItem("obsTelescope");
      if (tel) { const j = this.obs.findIndex((o) => o.telescope === tel); if (j >= 0) this.obsIdx = j; }
      // The real photo persists only across planet-to-planet hops (same-system links);
      // arriving from the gallery or a fresh visit always opens on the modelled render.
      const src = localStorage.getItem("heroSource");
      // The real photo persists only across planet-to-planet hops (above). The real map needs
      // no such carrying: it is this planet's default. What IS remembered is turning it OFF —
      // someone who wants the modelled globe keeps it, on every anchor, until they say
      // otherwise. A planet with no map has nothing to fall back from.
      this.heroSource =
        src === "telescope" && fromPlanet && this.obs.length ? "telescope"
        : src === "model" ? "model"
        : this._defaultSource();
      // Fetch the map up front so flipping the knob is instant, not a beat of schematic globe.
      if (this.map && window.PlanetRender) PlanetRender.preload(this.map);
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
    // ---- Reset the scope ----
    // Every knob carries across planet pages via localStorage, which is what makes a scope
    // set up three hops ago feel stuck: you can't tell which knob you turned. This puts the
    // instrument back to how it ships — full-spectrum channel, classic pixel render, the
    // planet's own star, the modelled picture, phase cycling from 20°. The stored keys are
    // cleared too, or the next planet page would just restore what was reset.
    _SCOPE_DEFAULTS: {
      view: "full", fidelity: "classic", heroStyle: "retro", illum: "native",
      obsIdx: 0, phaseIdx: 2, phasePlay: true,
    },
    // The Source knob's default is the one setting that depends on the planet: the five
    // anchors we have actually mapped open on their real map, matching the card you clicked
    // to get here. Everything else opens on the modelled render, having nothing else to show.
    _defaultSource() { return this.map ? "map" : "model"; },
    scopeDirty() {
      return this.heroSource !== this._defaultSource()
        || Object.keys(this._SCOPE_DEFAULTS).some((k) => this[k] !== this._SCOPE_DEFAULTS[k]);
    },
    resetScope() {
      Object.assign(this, this._SCOPE_DEFAULTS);
      this.heroSource = this._defaultSource();
      this._anim = null;  // let the phase cycle restart from the default position
      ["scopeView", "scopeIllum", "planetStyle", "renderFidelity", "heroSource", "obsTelescope"]
        .forEach((k) => { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } });
      this.blink();
      this._sweep();
      this.renderAll();
    },
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
      // Classic/Stylised restyles the SCHEMATIC bands, so it has nothing to say about a real
      // map either — both non-model sources bounce back to the render the knob acts on.
      if (this.heroSource !== "model") { this.heroSource = "model"; this._persist("heroSource", "model"); this.blink(); this.renderAll(); return; }
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
    // What this planet's Source knob can be turned to, in knob order. Most imaged planets
    // offer two positions; the five solar-system anchors, which have both a real map and a
    // real photograph, offer three. The knob is not rendered at all below two.
    sourceSteps() {
      return ["model"].concat(this.map ? ["map"] : [], this.obs.length ? ["telescope"] : []);
    },
    // Spread the available positions evenly across the knob's ±40° sweep, so a two-position
    // knob still reads as a two-position knob.
    sourceAngle() {
      const st = this.sourceSteps(), i = Math.max(0, st.indexOf(this.heroSource));
      return (st.length < 2 ? 0 : -40 + (80 * i) / (st.length - 1)) + "deg";
    },
    sourceLabel() {
      if (this.heroSource === "model") return "Modelled";
      if (this.heroSource === "map") return "Real map";
      return this.obs.length > 1 ? this.curObs().telescope : "Telescope";
    },
    // Jump straight to the real map (the hint line under the knobs). Idempotent: pressing it
    // while the map is already showing does nothing rather than cycling on to the photo.
    showMap() {
      if (!this.map || this.heroSource === "map") return;
      this.heroSource = "map";
      this._persist("heroSource", "map");
      this.blink();
      this.renderAll();
    },
    // Step the hero to the next source, wrapping back to the modelled render.
    toggleHeroSource() {
      const st = this.sourceSteps();
      if (st.length < 2) return;
      this.heroSource = st[(st.indexOf(this.heroSource) + 1) % st.length];
      this._persist("heroSource", this.heroSource);
      this.blink();
      this.renderAll();
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
    // --- Host star ("the lamp") panel ---------------------------------------------------
    // The lamp swatch follows the Light-source knob: the planet's own star, or the Sun when
    // the Sun-lit variant is on screen. The duotone planet ink stays pegged to the
    // full-spectrum colour (the Roman channel has no lamp of its own to show).
    lampHex() { return this.sunlit() ? this.sunLampHex : this.starHex; },
    lampLabel() { return this.sunlit() ? "The Sun · G2 V · 5772 K" : this.starLabel; },
    // The caption under the lamp. Swapped, this is NOT the light the planet reflects — it's
    // a hypothetical. Saying otherwise would be the one flat falsehood on the page, so the
    // wording flips with the knob and the real star stays named right beside it.
    lampCap() {
      return this.sunlit()
        ? "a stand-in — not the light this planet reflects"
        : "the light this planet reflects";
    },
    duoBase() { return this.sunlit() ? this.sunHex : this.fullHex; },
    copyDuo() {
      navigator.clipboard?.writeText(this.lampHex() + ", " + this.duoBase());
      this.flash("copied lamp + planet");
    },
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
      // Shared with the tour page's stop render — see PlanetRender.phaseCycle. Keeping the
      // arithmetic in one place is what stops the two from disagreeing about where the cycle
      // ends (the tour used to run all the way to the unlit disc).
      if (!this._anim) this._anim = PlanetRender.phaseCycle(this.phase().d, this.phases.length);
      const p = this._anim(t);
      if (p.idx !== this.phaseIdx) this.phaseIdx = p.idx;
      return {
        phase: p.rad,
        palette: this._phaseTint(this.curPalette(), p.idx),
        baseHex: this._phaseTint([this.curHex()], p.idx)[0],
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
    // Confirmation goes to the shared overlay toast (toast.js), never into the button row —
    // inline text there re-flowed the row on every copy.
    flash(m) { if (window.exoToast) window.exoToast(m); },
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
      // Must match _RAMP_ROLES in pipeline/palette/derive.py. No stop is called "base": the
      // ramp carries the planet's hue, not its exact colour, which is the swatch/hex above.
      const roles = ["shade-2", "shade-1", "mid", "tint-1", "tint-2"];
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
        // Retinted the same way as the palette, so haze/blueness tracks the phase colour.
        baseHex: this._phaseTint([this.curHex()])[0],
        radius: this.radius,
        cloudState: this.cloudState,
        lumY: this.curLum(),
        fidelity: this.fidelity,
        phase: (this.phase().d * Math.PI) / 180,
        // Real map only when the Source knob asks for it. baseHex above is what the map gets
        // rescaled to, so the mapped globe follows the view/illuminant/phase colour too.
        map: this.heroSource === "map" ? this.map : null,
        // A ringed planet always renders into its wide frame, even with the rings switched
        // off: the globe stays the size every other planet's is, and turning the Source knob
        // fills the sides in rather than reflowing the header around a box that changed shape.
        aspect: this.map && this.map.ring ? PlanetRender.ringAspect(this.map.ring) : 1,
      };
      // Single hero planet, rotating; its style (sphere/pixel) is a scope knob. When the
      // phase cycle is playing, the animator supplies a smoothly-advancing phase per frame.
      this.$refs.cHero.classList.toggle("pixel", this.heroStyle === "retro");
      const frame = this.phasePlay && this.phases.length > 1 ? (t) => this._phaseFrame(t) : null;
      PlanetRender.spin(this.$refs.cHero, { ...opts, style: this.heroStyle, frame: frame });
    },
  }));

  // "Your horizon" overlay for the sky chart: draws the observer's horizon — and shades the
  // ground below it — on the RA/dec map, for a chosen latitude at the visitor's current
  // clock time. Time comes from the device clock; east-west position is approximated from
  // the clock's UTC offset (15° of longitude per hour) — up to an hour of sky off under
  // daylight saving — or taken exactly from geolocation via "use my location".
  // Latitude is the slider, so the north/south difference is explicit, not assumed.
  Alpine.data("skyhorizon", () => ({
    sh: false,           // "how to read this chart" popover
    hz: false,           // horizon overlay on?
    lat: parseFloat(localStorage.getItem("skyLat") || defaultLat()),
    // Exact longitude from geolocation, if ever granted; null = fall back to the tz estimate.
    lon: localStorage.getItem("skyLon") != null ? parseFloat(localStorage.getItem("skyLon")) : null,
    geoAvail: !!(navigator.geolocation && navigator.geolocation.getCurrentPosition),
    geoState: "",        // "" | "busy" | "ok" | "err"
    tick: 0,             // bumped on every redraw so status() re-evaluates as time passes
    _timer: null,
    init() {
      // A stored longitude means a past "use my location" — reflect it on load, or a
      // refresh looks like the location was forgotten (it wasn't; it's still in use).
      if (this.lon != null) this.geoState = "ok";
      if (localStorage.getItem("skyHzn") === "1") this.toggleHzn(true);
    },
    // One-shot device location -> slider latitude + exact longitude. Explicit button press
    // only (the browser asks); the coordinates never leave the device — there is no server.
    useLocation() {
      if (!this.geoAvail || this.geoState === "busy") return;
      this.geoState = "busy";
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          // Slider range is ±65°; clamping only matters for polar visitors, whose sky the
          // chart edge distortion misrepresents anyway.
          this.lat = Math.max(-65, Math.min(65, Math.round(pos.coords.latitude)));
          this.lon = pos.coords.longitude;
          localStorage.setItem("skyLat", String(this.lat));
          localStorage.setItem("skyLon", String(this.lon));
          this.geoState = "ok";
          if (this.hz) this.draw();
        },
        () => { this.geoState = "err"; },
        { timeout: 12000, maximumAge: 600000 }
      );
    },
    geoLabel() {
      if (this.geoState === "busy") return "… locating";
      if (this.geoState === "ok") return "◎ located · " + this.latLabel();
      if (this.geoState === "err") return "◎ no location — use the slider";
      return "◎ Use my location";
    },
    destroy() { clearInterval(this._timer); },
    toggleHzn(force) {
      this.hz = force === true ? true : !this.hz;
      localStorage.setItem("skyHzn", this.hz ? "1" : "0");
      clearInterval(this._timer);
      if (this.hz) {
        this.draw();
        // The sky turns 0.25° per minute; redraw once a minute keeps the line honest.
        this._timer = setInterval(() => this.draw(), 60000);
      } else {
        this.$root.querySelectorAll(".skychart .hzn").forEach((g) => (g.innerHTML = ""));
      }
    },
    latChanged() {
      // A manual drag un-claims "located" (the label would lie); the exact longitude is
      // kept — moving the slider explores latitudes, it doesn't move you east-west.
      if (this.geoState === "ok") this.geoState = "";
      localStorage.setItem("skyLat", String(this.lat));
      if (this.hz) this.draw();
    },
    latLabel() {
      const a = Math.abs(this.lat);
      return a < 1 ? "the equator" : a + "° " + (this.lat > 0 ? "N" : "S");
    },
    // Thin wrappers over the shared ExoSky maths, bound to this panel's lat/lon.
    _lst() { return ExoSky.lstDeg(this.lon); },
    _alt(raDeg, decDeg) { return ExoSky.altAzDeg(raDeg, decDeg, this.lat, this.lon).alt; },
    status() {
      void this.tick;  // re-evaluate on every redraw
      const svg = this.$root.querySelector(".skychart");
      if (!svg || !this.hz) return "";
      const dec = +svg.dataset.dec, phi = this.lat;
      const from = "from " + this.latLabel();
      // Culmination bounds: never sets if |lat+dec| > 90, never rises if |lat-dec| > 90.
      if (Math.abs(phi - dec) > 90)
        return "This star NEVER RISES " + from + " — it belongs to the " +
          (dec > 0 ? "northern" : "southern") + " sky. Slide toward the " +
          (dec > 0 ? "north" : "south") + " and watch it climb above the ground.";
      if (Math.abs(phi + dec) > 90)
        return "Circumpolar " + from + ": this star never sets — above the horizon " +
          "all night, every night of the year.";
      const alt = this._alt(+svg.dataset.ra, dec);
      if (alt > 0)
        return "Above your horizon right now (about " + Math.round(alt) +
          "° up, " + from + ") — it sets as the sky turns.";
      return "Below your horizon right now, " + from + " — under the shaded ground. " +
        "The sky turns 15° per hour, so it rises later; check back tonight.";
    },
    draw() {
      this.tick++;
      const lst = this._lst();
      // At exactly 0° the horizon is a vertical wall in RA; 0.5° draws the same picture
      // without dividing by tan(0).
      const phi = Math.abs(this.lat) < 0.5 ? (this.lat < 0 ? -0.5 : 0.5) : this.lat;
      this.$root.querySelectorAll(".skychart").forEach((svg) => {
        const d = svg.dataset;
        const X0 = +d.x0, X1 = +d.x1, Y0 = +d.y0, Y1 = +d.y1;
        let pts = "";
        for (let ra = 360; ra >= 0; ra -= 2) {
          // Declination of the horizon at this RA: tan(dec) = -cos(H) / tan(lat).
          const decH = ExoSky.horizonDec(phi, lst, ra);
          const x = X0 + (1 - ra / 360) * (X1 - X0);
          const y = Y0 + ((90 - decH) / 180) * (Y1 - Y0);
          pts += x.toFixed(1) + "," + y.toFixed(1) + " ";
        }
        // The ground: close the curve along the edge holding the pole you can never see
        // (bottom for a northern observer, top for a southern one).
        const edge = phi > 0 ? Y1 : Y0;
        const floor = pts + X1.toFixed(1) + "," + edge + " " + X0.toFixed(1) + "," + edge;
        const lblY = phi > 0 ? +Y1 - 6 : +Y0 + 12;
        const lbl = svg.classList.contains("compact") ? "" :
          '<text class="hzn-lbl" x="' + (X0 + 8).toFixed(1) + '" y="' + lblY.toFixed(1) +
          '">GROUND — below your horizon</text>';
        svg.querySelector(".hzn").innerHTML =
          '<polygon class="hzn-floor" points="' + floor + '"/>' +
          '<polyline class="hzn-line" points="' + pts.trim() + '"/>' + lbl;
      });
    },
  }));

  // Best-guess starting latitude from the browser's timezone name — just a friendlier
  // default for the slider; the visitor corrects it with one drag. Falls back to 40° N.
  function defaultLat() {
    let tz = "";
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { /* old browsers */ }
    if (/Australia|Auckland|Johannesburg|Santiago|Buenos_Aires|Sao_Paulo|Lima|Harare|Nairobi/.test(tz))
      return "-30";
    return "40";
  }
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
      // The fragment is static HTML carrying BOTH colours; the current view decides which one
      // shows (CSS on the data-view attribute) so a peek never contradicts the card behind it.
      var view = window.__exoView === "roman" ? "roman" : "full";
      body.dataset.view = view;
      // The planet itself, drawn with the same engine + settings as the gallery cards.
      var cv = body.querySelector(".peek-planet");
      var pl = cv && window.PlanetRender && (window.PLANETS || []).find(function (x) {
        return x.id === cv.dataset.id;
      });
      if (pl) {
        var style = localStorage.getItem("planetStyle") || "retro";
        var roman = view === "roman" && pl.rhex;
        var base = roman ? pl.rhex : pl.hex;
        cv.classList.toggle("pixel", style === "retro");
        window.PlanetRender.render(cv, {
          palette: window.PlanetRender.ramp(base), baseHex: base,
          radius: pl.radius, cloudState: pl.cloud, lumY: roman ? pl.rlum : pl.lum,
          style: style, fidelity: localStorage.getItem("renderFidelity") || "classic",
          phase: window.exoCardPhase(pl.id),
          map: window.exoMap(pl.id), aspect: window.exoCardAspect(pl.id),
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
  var hovered = null;
  function optsFor(cv) {
    var list = window.PLANETS || [];
    var p = null;
    for (var i = 0; i < list.length; i++) if (list[i].id === cv.dataset.id) { p = list[i]; break; }
    if (!p) return null;
    // Read the view every time rather than caching it: this runs outside the Alpine component,
    // so a card spun up mid-session must use whatever the switch says NOW. Getting this wrong
    // is visible — the planet would snap back to its full-spectrum colours under the cursor.
    var roman = window.__exoView === "roman" && p.rhex;
    var base = roman ? p.rhex : p.hex;
    return {
      palette: window.PlanetRender.ramp(base), baseHex: base,
      radius: p.radius, cloudState: p.cloud, lumY: roman ? p.rlum : p.lum,
      style: localStorage.getItem("planetStyle") || "retro",
      fidelity: localStorage.getItem("renderFidelity") || "classic",
      phase: window.exoCardPhase(p.id),
      map: window.exoMap(p.id), aspect: window.exoCardAspect(p.id),
    };
  }
  // Per-hover animator: the same cycle the hero and the tour stops run, from `startRad`. A
  // card has no per-phase colours to tint with, so only the geometry is used here.
  function phaseAnimator(startRad) {
    var step = window.PlanetRender.phaseCycle((startRad * 180) / Math.PI);
    return function (t) { return { phase: step(t).rad }; };
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
