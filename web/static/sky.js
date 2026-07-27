// "Your sky tonight" (/sky.html): the whole catalog filtered to what is above the
// visitor's horizon right now. Location: latitude slider + tz-estimated longitude,
// or exact via one-shot geolocation (shared localStorage keys with the planet-page
// horizon overlay, so the two stay in sync). Sky maths come from window.ExoSky (app.js).
// Plain JS like census.js — the chart is rebuilt wholesale on every state change.

(function () {
  "use strict";

  // Chart geometry (SVG viewBox units), same conventions as the server-rendered charts:
  // RA increases LEFTWARD, 24h at the left edge, 0h at the right.
  // Padding is deliberately thin: the vertical scale is an HTML overlay (see .skp-yaxis),
  // so an outer gutter would be dead space — and on a zoomed-in phone view every unit of
  // padding costs several pixels of sky.
  var W = 900, H = 400, PL = 8, PR = 8, PT = 8, PB = 20;
  var X0 = PL, X1 = W - PR, Y0 = PT, Y1 = H - PB;
  var MAG = { eye: 6.5, bino: 9.5, any: Infinity };
  var MAG_NAME = { eye: "to the naked eye under a dark sky", bino: "with binoculars", any: "with a telescope" };
  // Bands from least to most equipment; a star needs the first one its magnitude fits in.
  var BANDS = ["eye", "bino", "any"];
  var BAND_BTN = { eye: "Naked eye", bino: "Binoculars", any: "Telescope" };
  function bandFor(vmag) {
    if (vmag == null) return null;         // no measured brightness: nothing to point at
    return vmag <= MAG.eye ? "eye" : vmag <= MAG.bino ? "bino" : "any";
  }

  function xOf(ra) { return X0 + (1 - (((ra % 360) + 360) % 360) / 360) * (X1 - X0); }
  function yOf(dec) { return Y0 + ((90 - dec) / 180) * (Y1 - Y0); }

  // "Standing outside" projection: azimuth across (N → E → S → W → N), altitude up,
  // the ground a flat strip along the bottom (ALT_MIN below the horizon line) — just deep
  // enough to read as ground; every extra degree steals sky.
  var ALT_MIN = -4;
  function xAz(az) { return X0 + (((az % 360) + 360) % 360) / 360 * (X1 - X0); }
  function yAlt(alt) { return Y0 + ((90 - alt) / (90 - ALT_MIN)) * (Y1 - Y0); }

  window.skyInit = function (cfg) {
    var hosts = [];        // [{name, ra, dec, vmag, planets:[{id,name,hex}], alt, az, vis}]
    var lat = parseFloat(localStorage.getItem("skyLat") || "40");
    var lon = localStorage.getItem("skyLon") != null ? parseFloat(localStorage.getItem("skyLon")) : null;
    var mag = localStorage.getItem("skyMag") || "eye";
    // "out" (default): the sky as you face it, flat horizon, only what's observable.
    // "map": the whole celestial sphere with the horizon curved across it.
    var view = localStorage.getItem("skyView") || "out";
    // A stored longitude means a past "use my location" — show the button as located on
    // load, or a refresh looks like the location was forgotten (it wasn't).
    var geoState = lon != null ? "ok" : "";
    var selected = null;   // hosts shown in the "at that spot" panel

    // ── arriving from a planet page: /sky.html?planet=<id> (or ?host=<star name>) ──
    // The visitor asked for one specific star, so the page opens pointed at it: crosshaired
    // and centred, in the view that can actually show it, with the band widened to the least
    // equipment that reaches it. Band and view are set in memory only — a deep link must not
    // rewrite the preferences the visitor set on their own.
    var q = new URLSearchParams(location.search);
    var wantPlanet = q.get("planet"), wantHost = q.get("host");
    var focus = null;          // the host star they came to find
    var focusWorld = null;     // the planet whose page they came from, when named
    var focusBand = null;      // band we widened to for it, if we did
    var focusCentred = false;  // viewBox already moved onto it
    var viewByUser = false;    // they have since worked the VIEW control themselves

    // A host's chart position in the current projection; null = not drawn (below the
    // horizon in the outside view — that sky simply doesn't exist for the observer).
    function posOf(h) {
      if (view === "out") return h.alt > 0 ? { x: xAz(h.az), y: yAlt(h.alt) } : null;
      return { x: xOf(h.ra), y: yOf(h.dec) };
    }

    var $ = function (id) { return document.getElementById(id); };
    var chartEl = $("skp-chart"), tipEl = $("skp-tip");

    // ── data ──────────────────────────────────────────────────────────────
    fetch(cfg.indexUrl).then(function (r) { return r.json(); }).then(function (planets) {
      var byHost = {};
      planets.forEach(function (p) {
        if (p.ra == null) return;
        var h = byHost[p.host] || (byHost[p.host] = {
          name: p.host, ra: p.ra, dec: p.dec, vmag: p.vmag != null ? p.vmag : null, planets: [],
        });
        h.planets.push({ id: p.id, name: p.name, hex: p.hex });
      });
      hosts = Object.values(byHost);
      if (wantPlanet || wantHost) {
        var hostName = wantHost;
        if (wantPlanet) {
          planets.some(function (p) {
            if (p.id !== wantPlanet) return false;
            hostName = p.host; focusWorld = p; return true;
          });
        }
        hosts.some(function (h) { return h.name === hostName ? (focus = h, true) : false; });
        if (focus) aimAtFocus();
      }
      render();
      // The sky turns 0.25° per minute; keep the page honest while it sits open.
      setInterval(render, 60000);
    });

    // ── state → DOM ───────────────────────────────────────────────────────
    function recompute() {
      var lim = MAG[mag];
      hosts.forEach(function (h) {
        var aa = ExoSky.altAzDeg(h.ra, h.dec, lat, lon);
        h.alt = aa.alt; h.az = aa.az;
        // Never list a host with no measured brightness (microlensing: no light to point at).
        h.vis = h.alt > 0 && h.vmag != null && h.vmag <= lim;
      });
    }

    function latLabel() {
      var a = Math.abs(lat);
      return a < 1 ? "the equator" : a + "° " + (lat > 0 ? "N" : "S");
    }

    // ── the star a visitor arrived to find ────────────────────────────────
    // Widen the band to the least equipment that reaches it (never narrow one they already
    // chose — a telescope view still shows a naked-eye star), then pick the view.
    function aimAtFocus() {
      var need = bandFor(focus.vmag);
      if (need && BANDS.indexOf(need) > BANDS.indexOf(mag)) { mag = need; focusBand = need; }
      chooseFocusView();
    }
    // Above the horizon → "standing outside", the view that shows it where you'd look for it.
    // Below → the whole-sky map, the only view in which sky under your feet exists at all.
    // Once the visitor works the VIEW control themselves, that choice stands.
    function chooseFocusView() {
      if (!focus || viewByUser) return;
      var next = ExoSky.altAzDeg(focus.ra, focus.dec, lat, lon).alt > 0 ? "out" : "map";
      if (next !== view) { view = next; vb = null; }
      focusCentred = false;
    }
    // Hours until this star next climbs above the horizon; null if it never sets (already
    // handled: it would be up) or never rises at all from this latitude.
    function hoursToRise(h) {
      var r = Math.PI / 180;
      var c = -Math.tan(lat * r) * Math.tan(h.dec * r);
      if (c <= -1 || c >= 1) return null;
      var H0 = Math.acos(c) / r;                                      // hour angle at rising
      var H = ((ExoSky.lstDeg(lon) - h.ra) % 360 + 540) % 360 - 180;  // hour angle now
      return (((-H0 - H) % 360 + 360) % 360) / 15.041;                // Earth turns 15.041°/h
    }
    function riseWords(h) {
      var t = hoursToRise(h);
      if (t == null) return "It never rises from this latitude — it belongs to the other " +
        "hemisphere's sky.";
      if (t < 1) return "It rises in about " + Math.max(1, Math.round(t * 60)) + " minutes, " +
        "in the east.";
      var hh = Math.floor(t), mm = Math.round((t - hh) * 60);
      if (mm === 60) { hh += 1; mm = 0; }
      return "It rises in about " + hh + " h" + (mm ? " " + mm + " m" : "") + ", in the east.";
    }

    function drawFocus() {
      var box = $("skp-focus");
      if (!focus) { box.hidden = true; return; }
      box.hidden = false;
      $("skp-focus-title").textContent = focusWorld
        ? "The star " + focusWorld.name + " orbits" : "The star you came for";

      var where = focus.alt > 0
        ? "<b>Above your horizon right now</b> — " + Math.round(focus.alt) + "° up, facing " +
          ExoSky.compass(focus.az) + ". The crosshair on the map is it."
        : "<b>Below your horizon right now</b> from " + latLabel() + ", so the whole-sky map " +
          "is showing instead of the outside view — the crosshair marks where it sits on the " +
          "celestial sphere. " + riseWords(focus);
      if (lon == null) {
        where += " Your east–west position is estimated from your device's clock — press " +
          "◎ Use my location for the real thing.";
      }

      var need = bandFor(focus.vmag), gear;
      if (need == null) {
        gear = "This star has <b>no measured visual brightness</b> in the catalog — some " +
          "hosts (microlensing detections, very faint or very red stars) simply carry no V " +
          "magnitude — so it is never listed as visible here. Its position is still real.";
      } else {
        gear = "At magnitude <b>V " + focus.vmag.toFixed(1) + "</b> it takes " +
          (need === "eye" ? "<b>no equipment at all</b> — naked-eye under a dark sky"
            : need === "bino" ? "<b>binoculars</b> — too faint for the eye"
            : "<b>a telescope</b> — well past binocular reach") + ".";
        if (focusBand) gear += " The band is set to " + BAND_BTN[focusBand] + " for you.";
      }

      // The one line that always shows: which star, where to look, what it takes. Everything
      // else is the detail — open on desktop, behind the ℹ on a phone.
      $("skp-focus-lead").innerHTML =
        '<span class="skp-focus-star">' + focus.name + "</span> · " +
        (focus.alt > 0
          ? Math.round(focus.alt) + "° up, facing " + ExoSky.compass(focus.az)
          : "below your horizon now") + " · " +
        (need == null ? "no brightness measured"
          : need === "eye" ? "naked eye" : need === "bino" ? "binoculars" : "telescope");
      $("skp-focus-body").innerHTML =
        "<p>" + where + "</p><p>" + gear + "</p>" +
        "<p>What you could ever see is the star itself — no exoplanet is visible to the eye " +
        "through any telescope. " + focus.name + " carries " + focus.planets.length +
        (focus.planets.length === 1 ? " known world" : " known worlds") + ":</p>" +
        worldChips(focus);
    }

    // Centre the viewport on the focused star, zoomed one step in so it is picked out of the
    // field. Runs once per view change, never on the minute tick — the map must not yank
    // itself back while someone is panning around.
    function centreOnFocus() {
      if (!focus || focusCentred) return;
      var p = posOf(focus);
      if (!p) { focusCentred = true; return; }   // below the horizon in the outside view
      var w = maxVbW() / 2;
      vb = { x: p.x - w / 2, y: 0, w: w, h: 0 };
      clampVb();                                  // derives the height from the container
      vb.y = p.y - vb.h / 2;
      applyVb();
      focusCentred = true;
    }

    function render() {
      recompute();
      $("skp-latlbl").textContent = latLabel();
      $("skp-lat").value = lat;
      document.querySelectorAll(".skp-mag-btn[data-mag]").forEach(function (b) {
        b.classList.toggle("on", b.dataset.mag === mag);
        var led = b.querySelector(".led");
        if (led) led.classList.toggle("on", b.dataset.mag === mag);
      });
      // The VIEW knob: rotate to the current position, name it in plain English. Its
      // phone-only twin under the chart names the view you'd switch TO.
      var knob = $("skp-viewknob");
      if (knob) {
        knob.style.setProperty("--a", view === "out" ? "-34deg" : "34deg");
        $("skp-viewval").textContent = view === "out" ? "Standing outside" : "Whole-sky map";
      }
      document.querySelectorAll(".skp-view-btn[data-view]").forEach(function (b) {
        var on = b.dataset.view === view;
        b.classList.toggle("on", on);
        var l = b.querySelector(".led");
        if (l) l.classList.toggle("on", on);
      });

      var vis = hosts.filter(function (h) { return h.vis; })
        .sort(function (a, b) { return a.vmag - b.vmag; });
      var above = hosts.filter(function (h) { return h.alt > 0; }).length;
      var nWorlds = vis.reduce(function (n, h) { return n + h.planets.length; }, 0);
      // The count lives in the list heading; the full honest sentence behind its ℹ.
      $("skp-count-full").innerHTML =
        "<b>" + vis.length + "</b> of this catalog's " + hosts.length + " host stars are " +
        "visible " + MAG_NAME[mag] + " from " + latLabel() + " right now, carrying <b>" +
        nWorlds + "</b> known worlds. " + above + " hosts are above your horizon at any " +
        "brightness. What you could ever see is the star — no exoplanet is visible to the " +
        "eye through any telescope.";

      drawChart(vis);
      centreOnFocus();
      drawFocus();
      drawList(vis);
      drawSpot();
    }

    // Horizon line + ground polygon + label position for the current lat/lon, in SVG units.
    function horizonGeom() {
      var phi = Math.abs(lat) < 0.5 ? (lat < 0 ? -0.5 : 0.5) : lat;
      var lst = ExoSky.lstDeg(lon);
      var pts = "";
      for (var ra = 360; ra >= 0; ra -= 2) {
        pts += xOf(ra === 360 ? 359.999 : ra).toFixed(1) + "," +
          yOf(ExoSky.horizonDec(phi, lst, ra)).toFixed(1) + " ";
      }
      pts = pts.replace(/^([\d.]+),/, X0 + ",");  // pin the first sample to the exact left edge
      var edge = phi > 0 ? Y1 : Y0;
      return {
        line: pts.trim(),
        floor: pts + X1 + "," + edge + " " + X0 + "," + edge,
      };
    }

    // Cheap per-drag update: move only the horizon line and ground shading in place, leaving
    // the ~4k star dots alone. The full render (dot visibility, counts, lists) is debounced
    // until the slider rests — rebuilding the whole SVG per input event visibly lags.
    function updateHorizonOnly() {
      $("skp-latlbl").textContent = latLabel();
      // Outside view: the horizon is flat and static — it's the STARS that move with
      // latitude, and that rebuild is exactly what the debounced render is for.
      if (view === "out") return;
      var svg = chartEl.querySelector("svg");
      if (!svg) return;
      var g = horizonGeom();
      svg.querySelector(".hzn-line").setAttribute("points", g.line);
      svg.querySelector(".hzn-floor").setAttribute("points", g.floor);
    }

    function drawChart(vis) {
      var s = '<svg viewBox="0 0 ' + W + " " + H + '" class="skychart" role="img" ' +
        'aria-label="' + (view === "out"
          ? "Your observable sky: catalog host stars by compass direction and height"
          : "Sky map: catalog host stars above your horizon right now") + '">' +
        '<rect x="' + X0 + '" y="' + Y0 + '" width="' + (X1 - X0) + '" height="' + (Y1 - Y0) +
        '" class="skyframe"/>';
      var groundLine, groundFloor;

      if (view === "out") {
        // Compass across the bottom, altitude up, the ground a flat strip.
        var COMP = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"];
        for (var i = 0; i <= 8; i++) {
          var xa = i === 8 ? X1 : xAz(i * 45);
          s += '<line x1="' + xa.toFixed(1) + '" y1="' + Y0 + '" x2="' + xa.toFixed(1) +
            '" y2="' + Y1 + '" class="grid"/>';
          var aa = i === 0 ? "start" : i === 8 ? "end" : "middle";
          s += '<text x="' + xa.toFixed(1) + '" y="' + (H - 6) + '" class="tick" ' +
            'text-anchor="' + aa + '">' + COMP[i] + "</text>";
        }
        [30, 60].forEach(function (alt) {
          var ya = yAlt(alt);
          s += '<line x1="' + X0 + '" y1="' + ya.toFixed(1) + '" x2="' + X1 + '" y2="' +
            ya.toFixed(1) + '" class="grid"/>';
          // No in-SVG label: the vertical scale is an HTML overlay (drawYAxis).
        });
        var gy = yAlt(0).toFixed(1);
        groundLine = X0 + "," + gy + " " + X1 + "," + gy;
        groundFloor = X0 + "," + gy + " " + X1 + "," + gy + " " + X1 + "," + Y1 + " " + X0 + "," + Y1;
      } else {
        for (var hr = 0; hr <= 24; hr += 3) {
          var xx = X0 + (1 - hr / 24) * (X1 - X0);
          s += '<line x1="' + xx + '" y1="' + Y0 + '" x2="' + xx + '" y2="' + Y1 + '" class="grid"/>';
          if (hr % 6 === 0) {
            var anch = hr === 24 ? "start" : hr === 0 ? "end" : "middle";
            s += '<text x="' + xx + '" y="' + (H - 6) + '" class="tick" text-anchor="' + anch + '">' + hr + "h</text>";
          }
        }
        [-60, -30, 0, 30, 60].forEach(function (dec) {
          var yy = yOf(dec);
          s += '<line x1="' + X0 + '" y1="' + yy.toFixed(1) + '" x2="' + X1 + '" y2="' + yy.toFixed(1) +
            '" class="grid' + (dec === 0 ? " eq" : "") + '"/>';
          // Labels come from the HTML overlay (drawYAxis), not the canvas.
        });
        var g = horizonGeom();
        groundLine = g.line;
        groundFloor = g.floor;
      }

      // Ground first (under the dots), then dim dots, horizon line, lit dots on top.
      s += '<polygon class="hzn-floor" points="' + groundFloor + '"/>';
      // Dots in the current projection; posOf returns null for sky the observer can't see.
      var dim = "", lit = "";
      hosts.forEach(function (h, i) {
        var p = posOf(h);
        if (!p) return;
        var x = p.x.toFixed(1), y = p.y.toFixed(1);
        if (h.vis) {
          lit += '<circle cx="' + x + '" cy="' + y + '" r="3" class="skp-dot-vis" data-i="' + i + '"/>';
        } else {
          dim += '<rect x="' + (x - 1) + '" y="' + (y - 1) + '" width="2" height="2" class="skydot"/>';
        }
      });
      // No in-SVG ground label: the legend is a screen-pinned overlay in the template, so
      // panning and zooming can never move it out of view.
      s += dim + '<polyline class="hzn-line" points="' + groundLine + '"/>' + lit;
      // Crosshair on the star this visit is about, on top of everything and inert to clicks
      // (the dot underneath keeps taking them). Its scale is set in applyVb.
      var fp = focus && posOf(focus);
      if (fp) {
        // Drawn twice: a dark backing pass so the mark survives the Kepler field (hundreds of
        // lit dots packed into one patch), then the amber one over it.
        var arms = '<circle cx="0" cy="0" r="10"/>' +
          '<line x1="0" y1="-22" x2="0" y2="-14"/><line x1="0" y1="14" x2="0" y2="22"/>' +
          '<line x1="-22" y1="0" x2="-14" y2="0"/><line x1="14" y1="0" x2="22" y2="0"/>';
        s += '<g class="skp-focus-mark" pointer-events="none" data-x="' + fp.x.toFixed(1) +
          '" data-y="' + fp.y.toFixed(1) + '" transform="translate(' + fp.x.toFixed(1) + " " +
          fp.y.toFixed(1) + ')"><g class="fm-back">' + arms + "</g>" + arms + "</g>";
      }
      chartEl.innerHTML = s + "</svg>";
      applyVb();
    }

    // ── pan & zoom: the chart is a viewport onto the sky, driven via the viewBox ──────
    // On a phone the container is tall and full-bleed, so "fit" already means zoomed into
    // a pannable strip (full declination range, drag through RA); on desktop "fit" is the
    // whole map. The viewBox aspect always matches the container, so nothing distorts.
    var vb = null;  // {x, y, w, h} in SVG units; null until first laid out
    function maxVbW() {
      var rect = chartEl.getBoundingClientRect();
      if (!rect.width || !rect.height) return W;
      return Math.min(W, H * rect.width / rect.height);
    }
    function clampVb() {
      var rect = chartEl.getBoundingClientRect();
      vb.w = Math.max(120, Math.min(vb.w, maxVbW()));
      vb.h = rect.width ? Math.min(H, vb.w * rect.height / rect.width) : H;
      vb.x = Math.max(0, Math.min(vb.x, W - vb.w));
      vb.y = Math.max(0, Math.min(vb.y, H - vb.h));
    }
    function applyVb() {
      var svg = chartEl.querySelector("svg");
      if (!svg) return;
      if (!vb) {
        // First layout: fit. Outside view centres on where your visible sky is deepest
        // (south for a northern observer, north for a southern one); the map centres on
        // what is crossing your meridian right now.
        vb = { w: maxVbW(), h: 0, x: 0, y: 0 };
        vb.x = (view === "out" ? xAz(lat >= 0 ? 180 : 0) : xOf(ExoSky.lstDeg(lon))) - vb.w / 2;
      }
      clampVb();
      svg.setAttribute("viewBox",
        vb.x.toFixed(1) + " " + vb.y.toFixed(1) + " " + vb.w.toFixed(1) + " " + vb.h.toFixed(1));
      // While the full declination range is in view there is no vertical pan to give, so
      // vertical touch drags stay with the browser (page scroll). Only a vertically zoomed
      // view claims them.
      svg.style.touchAction = vb.h >= H - 0.5 ? "pan-y" : "none";
      // Dots shrink (in SVG units) as you zoom, so they stay dot-sized on screen.
      var s = Math.sqrt(vb.w / maxVbW());
      chartEl.style.setProperty("--skp-rvis", (3 * Math.max(0.45, s)).toFixed(2) + "px");
      chartEl.style.setProperty("--skp-rdim", (2 * Math.max(0.5, s)).toFixed(2) + "px");
      // The crosshair is drawn at a fixed size in SVG units, so rescale it the same way the
      // dots are — otherwise zooming in blows it up off the screen.
      var fm = svg.querySelector(".skp-focus-mark");
      if (fm) {
        fm.setAttribute("transform", "translate(" + fm.dataset.x + " " + fm.dataset.y +
          ") scale(" + Math.max(0.45, s).toFixed(3) + ")");
      }
      // Axis labels are sized in SVG units, so a zoomed-in view magnifies them — worst on
      // a phone, where the fit is already zoomed. Convert a fixed screen size into the
      // current viewBox's units instead, so ticks stay small at every zoom.
      var rect2 = chartEl.getBoundingClientRect();
      var tickPx = matchMedia("(max-width: 760px)").matches ? 8 : 9.5;
      chartEl.style.setProperty("--skp-tick",
        (tickPx * vb.w / (rect2.width || W)).toFixed(2) + "px");
      // Altitude / declination labels ride the viewport's left edge, so panning east-west
      // never leaves the vertical scale unreadable.
      drawYAxis();
    }
    // The vertical scale, as HTML pinned over the chart's left edge: each tick's canvas y
    // becomes a percentage of the current viewBox, so it stays put through pans and zooms
    // and never shrinks below legibility.
    function drawYAxis() {
      var box = $("skp-yaxis");
      if (!box || !vb) return;
      var ticks = view === "out"
        ? [[yAlt(60), "60°"], [yAlt(30), "30°"], [yAlt(0), "horizon"]]
        : [[yOf(60), "+60°"], [yOf(30), "+30°"], [yOf(0), "0°"],
           [yOf(-30), "−30°"], [yOf(-60), "−60°"]];
      box.innerHTML = ticks.map(function (t) {
        var pct = (t[0] - vb.y) / vb.h * 100;
        if (pct < 2 || pct > 98) return "";  // off the current viewport
        return '<span style="top:' + pct.toFixed(2) + '%">' + t[1] + "</span>";
      }).join("");
    }

    function zoomBy(f) {
      if (!vb) return;
      var cx = vb.x + vb.w / 2, cy = vb.y + vb.h / 2;
      vb.w /= f; vb.h /= f;
      vb.x = cx - vb.w / 2; vb.y = cy - vb.h / 2;
      applyVb();
    }
    $("skp-zin").addEventListener("click", function () { zoomBy(1.5); });
    $("skp-zout").addEventListener("click", function () { zoomBy(1 / 1.5); });
    $("skp-zfit").addEventListener("click", function () { vb = null; applyVb(); });
    window.addEventListener("resize", function () { if (vb) applyVb(); });

    // One pointer drags; two pinch. No wheel zoom — the mouse wheel must keep scrolling
    // the page (zoom is the buttons or a pinch).
    var pointers = new Map();  // pointerId -> {x, y}
    var drag = null, pinch = null, dragged = false;
    function pinchMid() {
      var pts = [...pointers.values()];
      return { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2,
               d: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) };
    }
    chartEl.addEventListener("pointerdown", function (e) {
      if (!vb) return;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      try { chartEl.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events */ }
      if (pointers.size === 2) {
        var rect = chartEl.getBoundingClientRect(), m = pinchMid();
        // Anchor: the sky position under the fingers' midpoint stays under it.
        pinch = {
          d0: m.d, w0: vb.w,
          px: vb.x + (m.x - rect.left) / rect.width * vb.w,
          py: vb.y + (m.y - rect.top) / rect.height * vb.h,
        };
        drag = null;
        dragged = true;  // a pinch is not a pick either
      } else if (pointers.size === 1) {
        drag = { x: e.clientX, y: e.clientY, vx: vb.x, vy: vb.y };
        dragged = false;
      }
      chartEl.classList.add("dragging");
    });
    chartEl.addEventListener("pointermove", function (e) {
      if (!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      var rect = chartEl.getBoundingClientRect();
      if (pinch && pointers.size === 2) {
        var m = pinchMid();
        vb.w = pinch.w0 * pinch.d0 / Math.max(1, m.d);
        clampVb();  // derives vb.h from the new width
        vb.x = pinch.px - (m.x - rect.left) / rect.width * vb.w;
        vb.y = pinch.py - (m.y - rect.top) / rect.height * vb.h;
        applyVb();
      } else if (drag) {
        // Only a deliberate pan swallows the click — a shaky-hand 3-4px wobble must not.
        if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) > 8) dragged = true;
        vb.x = drag.vx - (e.clientX - drag.x) * vb.w / rect.width;
        vb.y = drag.vy - (e.clientY - drag.y) * vb.h / rect.height;
        applyVb();
      }
    });
    ["pointerup", "pointercancel"].forEach(function (ev) {
      chartEl.addEventListener(ev, function (e) {
        pointers.delete(e.pointerId);
        pinch = null;
        // Falling from a pinch to one finger restarts a plain drag from here.
        if (pointers.size === 1 && vb) {
          var p = [...pointers.values()][0];
          drag = { x: p.x, y: p.y, vx: vb.x, vy: vb.y };
        } else {
          drag = null;
        }
        if (!pointers.size) chartEl.classList.remove("dragging");
      });
    });

    function starMeta(h) {
      return "V " + h.vmag.toFixed(1) + " · " + Math.round(h.alt) + "° up, facing " +
        ExoSky.compass(h.az) + " · " + h.planets.length +
        (h.planets.length === 1 ? " world" : " worlds");
    }

    function worldChips(h) {
      return '<span class="skp-worlds">' + h.planets.map(function (p) {
        return '<a class="skp-world" href="/planet/' + p.id + '">' +
          '<span class="sw" style="background:' + p.hex + '"></span>' + p.name + "</a>";
      }).join("") + "</span>";
    }

    function rowHtml(h) {
      return '<div class="skp-row"><span class="skp-star">' +
        (h.vmag <= 6.5 ? '<span class="skp-eye" title="Naked-eye star">◉ </span>' : "") +
        h.name + '</span><span class="skp-meta">' + starMeta(h) + "</span>" + worldChips(h) + "</div>";
    }

    function drawList(vis) {
      // "92 of 4274 stars"; when everything shows, just "4274 stars".
      var count = vis.length === hosts.length
        ? hosts.length + (hosts.length === 1 ? " star" : " stars")
        : vis.length + " of " + hosts.length + " stars";
      $("skp-list-title").textContent =
        "Visible " + MAG_NAME[mag].replace("to the ", "") + " · " + count;
      $("skp-list").innerHTML = vis.length
        ? vis.map(rowHtml).join("")
        : '<p class="skp-empty">Nothing above your horizon passes this filter right now — ' +
          "try a wider one, or check back in a few hours (the sky turns 15° per hour).</p>";
    }

    function drawSpot() {
      var panel = $("skp-spot-panel");
      if (!selected || !selected.length) { panel.hidden = true; return; }
      panel.hidden = false;
      $("skp-spot-title").textContent = "At that spot · " + selected.length +
        (selected.length === 1 ? " star" : " stars");
      $("skp-spot").innerHTML = selected.map(rowHtml).join("");
    }

    // ── interactions ──────────────────────────────────────────────────────
    // One tooltip, two modes. Hovering previews a star (inert, follows the cursor);
    // clicking or tapping PINS it, and the worlds become real links — which is the whole
    // interaction on a phone, where there is no hover and the panel below is redundant.
    var pinned = false;

    // Worlds capped at 5 with an honest ellipsis (some systems carry 6+).
    function tipStar(h, linked) {
      var rows = h.planets.slice(0, 5).map(function (p) {
        var sw = '<span class="ct-sw" style="background:' + p.hex + '"></span>';
        return linked
          ? '<a class="ct-world" href="/planet/' + p.id + '">' + sw + p.name + "</a>"
          : sw + p.name;
      });
      if (h.planets.length > 5) {
        rows.push('<span class="ct-dim">… and ' + (h.planets.length - 5) + " more</span>");
      }
      return "<b>" + h.name + "</b><br><span class='ct-dim'>" + starMeta(h) + "</span><br>" +
        rows.join("<br>");
    }

    function placeTip(x, y) {
      var w = 250, h = tipEl.offsetHeight || 140;
      tipEl.style.left = Math.max(6, Math.min(x + 14, window.innerWidth - w - 6)) + "px";
      // Flip above the point when there is no room below.
      tipEl.style.top = (y + 14 + h > window.innerHeight ? Math.max(6, y - h - 10) : y + 14) + "px";
    }

    function hideTip() {
      pinned = false;
      tipEl.classList.remove("pinned");
      tipEl.style.display = "none";
    }

    chartEl.addEventListener("mousemove", function (e) {
      if (pinned) return;  // a pinned tooltip is not replaced by passing hovers
      var t = e.target.closest && e.target.closest(".skp-dot-vis");
      if (!t) { tipEl.style.display = "none"; return; }
      tipEl.innerHTML = tipStar(hosts[+t.dataset.i], false) +
        "<br><span class='ct-dim'>click to open</span>";
      tipEl.style.display = "block";
      placeTip(e.clientX, e.clientY);
    });
    chartEl.addEventListener("mouseleave", function () { if (!pinned) tipEl.style.display = "none"; });
    // Any tap outside the pinned tooltip dismisses it (the chart's own handler re-pins).
    document.addEventListener("pointerdown", function (e) {
      if (pinned && !tipEl.contains(e.target)) hideTip();
    }, true);
    chartEl.addEventListener("click", function (e) {
      if (dragged) { dragged = false; return; }  // a pan is not a pick
      var svg = chartEl.querySelector("svg");
      if (!svg) return;
      // Click in SVG coords; collect every visible star within a small radius, so one click
      // on a crowded patch (the Kepler field) opens all of it.
      var pt = svg.createSVGPoint();
      pt.x = e.clientX; pt.y = e.clientY;
      var p = pt.matrixTransform(svg.getScreenCTM().inverse());
      // Pick radius ≈ 9 screen px in current-viewBox SVG units, so taps work at any zoom.
      var R = Math.max(4, 9 * (vb ? vb.w : W) / svg.getBoundingClientRect().width);
      var picked = new Set();
      hosts.forEach(function (h, i) {
        if (!h.vis) return;
        var q = posOf(h);
        if (!q) return;
        var dx = q.x - p.x, dy = q.y - p.y;
        if (dx * dx + dy * dy <= R * R) picked.add(i);
      });
      selected = [...picked].map(function (i) { return hosts[i]; })
        .sort(function (a, b) { return a.vmag - b.vmag; });
      // Ring the picked dots so the tap visibly lands even before scrolling to the panel.
      svg.querySelectorAll(".skp-dot-vis").forEach(function (c) {
        c.classList.toggle("sel", picked.has(+c.dataset.i));
      });
      drawSpot();
      // Pin the tooltip at the tap with tappable worlds — on a phone this IS the result
      // (the panel below is hidden there); on desktop it doubles as the click affordance
      // the hover promised. No scrolling either way.
      if (selected.length) {
        var head = '<button class="ct-x" id="skp-tip-x" aria-label="Close">&times;</button>';
        var body = selected.slice(0, 3).map(function (h) { return tipStar(h, true); })
          .join('<span class="ct-sep"></span>');
        if (selected.length > 3) {
          body += '<span class="ct-sep"></span><span class="ct-dim">… and ' +
            (selected.length - 3) + " more stars at this spot</span>";
        }
        tipEl.innerHTML = head + body;
        tipEl.style.display = "block";
        pinned = true;
        tipEl.classList.add("pinned");
        placeTip(e.clientX, e.clientY);
        $("skp-tip-x").addEventListener("click", hideTip);
      } else {
        hideTip();
      }
    });
    $("skp-spot-x").addEventListener("click", function () {
      selected = null;
      var svg = chartEl.querySelector("svg");
      if (svg) svg.querySelectorAll(".skp-dot-vis.sel").forEach(function (c) {
        c.classList.remove("sel");
      });
      drawSpot();
    });

    // Phone-only ℹ: unfolds the where/equipment/worlds detail the desktop card shows outright.
    $("skp-focus-i").addEventListener("click", function () {
      var open = $("skp-focus").classList.toggle("open");
      this.classList.toggle("on", open);
      this.setAttribute("aria-expanded", open ? "true" : "false");
    });

    // Dismissing the arrived-at star drops the crosshair and the ?planet= from the URL, so a
    // reload doesn't drag it back.
    $("skp-focus-x").addEventListener("click", function () {
      focus = null; focusWorld = null; focusBand = null;
      if (history.replaceState) history.replaceState(null, "", location.pathname);
      render();
    });

    var latDebounce = null;
    $("skp-lat").addEventListener("input", function () {
      lat = +this.value;
      if (geoState === "ok") { geoState = ""; updateGeoBtn(); }
      localStorage.setItem("skyLat", String(lat));
      // Instant feedback (label + horizon curve); the expensive dot/list rebuild waits
      // until the slider has rested for a beat.
      updateHorizonOnly();
      clearTimeout(latDebounce);
      latDebounce = setTimeout(render, 180);
    });
    document.querySelectorAll(".skp-mag-btn[data-mag]").forEach(function (b) {
      b.addEventListener("click", function () {
        mag = b.dataset.mag;
        localStorage.setItem("skyMag", mag);
        selected = null;
        focusBand = null;   // they set the band themselves now; stop claiming we did
        render();
      });
    });
    // The VIEW knob toggles between the two projections (click, Enter, or Space).
    function setView(next) {
      if (next === view) return;
      view = next;
      localStorage.setItem("skyView", view);
      selected = null;
      vb = null;  // re-fit and re-centre for the new projection
      // Their choice now outranks the deep link's — but keep pointing at the star, in the
      // projection they just asked for.
      viewByUser = true;
      focusCentred = false;
      render();
    }
    function toggleView() { setView(view === "out" ? "map" : "out"); }
    var viewKnob = $("skp-viewknob");
    viewKnob.addEventListener("click", toggleView);
    viewKnob.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleView(); }
    });
    document.querySelectorAll(".skp-view-btn[data-view]").forEach(function (b) {
      b.addEventListener("click", function () { setView(b.dataset.view); });
    });

    $("skp-rx-info").addEventListener("click", function () {
      var bar = $("skp-rx-info-bar");
      bar.hidden = !bar.hidden;
      this.classList.toggle("on", !bar.hidden);
    });

    $("skp-count-info").addEventListener("click", function () {
      var full = $("skp-count-full");
      full.hidden = !full.hidden;
      this.classList.toggle("on", !full.hidden);
    });

    var geoBtn = $("skp-geo");
    if (!(navigator.geolocation && navigator.geolocation.getCurrentPosition)) geoBtn.hidden = true;
    function updateGeoBtn() {
      $("skp-geo-txt").textContent =
        geoState === "busy" ? "… locating" :
        geoState === "ok" ? "located · " + latLabel() :
        geoState === "err" ? "no location — tune the dial" : "Use my location";
      // The lamp: lit amber once located (see .skr-geo .led.on).
      $("skp-geo-led").classList.toggle("on", geoState === "ok");
      geoBtn.classList.toggle("on", geoState === "ok");
      geoBtn.disabled = geoState === "busy";
    }
    function locate() {
      if (geoState === "busy") return;
      geoState = "busy"; updateGeoBtn();
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          lat = Math.max(-65, Math.min(65, Math.round(pos.coords.latitude)));
          lon = pos.coords.longitude;
          localStorage.setItem("skyLat", String(lat));
          localStorage.setItem("skyLon", String(lon));
          geoState = "ok"; updateGeoBtn();
          // A real position can move the focused star across the horizon — re-decide the
          // view now that "your sky" means the actual one.
          if (focus) { recompute(); chooseFocusView(); }
          render();
        },
        function () { geoState = "err"; updateGeoBtn(); },
        { timeout: 12000, maximumAge: 600000 }
      );
    }
    geoBtn.addEventListener("click", locate);
    updateGeoBtn();

    // First-visit prompt: our own retro dialog, shown once — the browser's real permission
    // dialog only appears if the visitor says yes here. Any dismissal is remembered; never
    // shown again once a location is stored either.
    var modal = $("skp-modal");
    function closeModal() {
      modal.hidden = true;
      localStorage.setItem("skyGeoAsked", "1");
    }
    if (modal && !geoBtn.hidden && lon == null && !localStorage.getItem("skyGeoAsked")) {
      modal.hidden = false;
      $("skp-modal-yes").addEventListener("click", function () { closeModal(); locate(); });
      $("skp-modal-no").addEventListener("click", closeModal);
      $("skp-modal-x").addEventListener("click", closeModal);
      modal.addEventListener("click", function (e) { if (e.target === modal) closeModal(); });
    }
  };
})();
