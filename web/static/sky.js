// "Your sky tonight" (/sky.html): the whole catalog filtered to what is above the
// visitor's horizon right now. Location: latitude slider + tz-estimated longitude,
// or exact via one-shot geolocation (shared localStorage keys with the planet-page
// horizon overlay, so the two stay in sync). Sky maths come from window.ExoSky (app.js).
// Plain JS like census.js — the chart is rebuilt wholesale on every state change.

(function () {
  "use strict";

  // Chart geometry (SVG viewBox units), same conventions as the server-rendered charts:
  // RA increases LEFTWARD, 24h at the left edge, 0h at the right.
  var W = 900, H = 400, PL = 46, PR = 16, PT = 16, PB = 30;
  var X0 = PL, X1 = W - PR, Y0 = PT, Y1 = H - PB;
  var MAG = { eye: 6.5, bino: 9.5, any: Infinity };
  var MAG_NAME = { eye: "to the naked eye under a dark sky", bino: "with binoculars", any: "with a telescope" };

  function xOf(ra) { return X0 + (1 - (((ra % 360) + 360) % 360) / 360) * (X1 - X0); }
  function yOf(dec) { return Y0 + ((90 - dec) / 180) * (Y1 - Y0); }

  window.skyInit = function (cfg) {
    var hosts = [];        // [{name, ra, dec, vmag, planets:[{id,name,hex}], alt, az, vis}]
    var lat = parseFloat(localStorage.getItem("skyLat") || "40");
    var lon = localStorage.getItem("skyLon") != null ? parseFloat(localStorage.getItem("skyLon")) : null;
    var mag = localStorage.getItem("skyMag") || "eye";
    var geoState = "";
    var selected = null;   // hosts shown in the "at that spot" panel

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

    function render() {
      recompute();
      $("skp-latlbl").textContent = latLabel();
      $("skp-lat").value = lat;
      document.querySelectorAll(".skp-mag-btn").forEach(function (b) {
        b.classList.toggle("on", b.dataset.mag === mag);
      });

      var vis = hosts.filter(function (h) { return h.vis; })
        .sort(function (a, b) { return a.vmag - b.vmag; });
      var above = hosts.filter(function (h) { return h.alt > 0; }).length;
      var nWorlds = vis.reduce(function (n, h) { return n + h.planets.length; }, 0);
      $("skp-count").innerHTML =
        "<b>" + vis.length + "</b> of this catalog's " + hosts.length + " host stars are " +
        "visible " + MAG_NAME[mag] + " from " + latLabel() + " right now, carrying <b>" +
        nWorlds + "</b> known worlds (" + above + " are above your horizon at any brightness).";

      drawChart(vis);
      drawList(vis);
      drawSpot();
    }

    function drawChart(vis) {
      var phi = Math.abs(lat) < 0.5 ? (lat < 0 ? -0.5 : 0.5) : lat;
      var lst = ExoSky.lstDeg(lon);
      var s = '<svg viewBox="0 0 ' + W + " " + H + '" class="skychart" role="img" ' +
        'aria-label="Sky map: catalog host stars above your horizon right now">' +
        '<rect x="' + X0 + '" y="' + Y0 + '" width="' + (X1 - X0) + '" height="' + (Y1 - Y0) +
        '" class="skyframe"/>';
      for (var hr = 0; hr <= 24; hr += 3) {
        var xx = X0 + (1 - hr / 24) * (X1 - X0);
        s += '<line x1="' + xx + '" y1="' + Y0 + '" x2="' + xx + '" y2="' + Y1 + '" class="grid"/>';
        if (hr % 6 === 0) {
          var anch = hr === 24 ? "start" : hr === 0 ? "end" : "middle";
          s += '<text x="' + xx + '" y="' + (H - 8) + '" class="tick" text-anchor="' + anch + '">' + hr + "h</text>";
        }
      }
      [-60, -30, 0, 30, 60].forEach(function (dec) {
        var yy = yOf(dec);
        s += '<line x1="' + X0 + '" y1="' + yy.toFixed(1) + '" x2="' + X1 + '" y2="' + yy.toFixed(1) +
          '" class="grid' + (dec === 0 ? " eq" : "") + '"/>';
        if (dec % 60 === 0) {
          s += '<text x="' + (X0 - 5) + '" y="' + (yy + 3).toFixed(1) + '" class="tick" text-anchor="end">' +
            (dec ? (dec > 0 ? "+" : "") + dec + "°" : "0°") + "</text>";
        }
      });

      // Ground first (under the dots): same construction as the planet-page overlay.
      var pts = "";
      for (var ra = 360; ra >= 0; ra -= 2) {
        pts += xOf(ra === 360 ? 359.999 : ra).toFixed(1) + "," + yOf(ExoSky.horizonDec(phi, lst, ra)).toFixed(1) + " ";
      }
      pts = pts.replace(/^([\d.]+),/, X0 + ",");  // pin the first sample to the exact left edge
      var edge = phi > 0 ? Y1 : Y0;
      s += '<polygon class="hzn-floor" points="' + pts + X1 + "," + edge + " " + X0 + "," + edge + '"/>';

      // Dots: dim = below horizon or too faint; accent = visible under the current filter.
      var dim = "", lit = "";
      hosts.forEach(function (h, i) {
        var x = xOf(h.ra).toFixed(1), y = yOf(h.dec).toFixed(1);
        if (h.vis) {
          lit += '<circle cx="' + x + '" cy="' + y + '" r="3" class="skp-dot-vis" data-i="' + i + '"/>';
        } else {
          dim += '<rect x="' + (x - 1) + '" y="' + (y - 1) + '" width="2" height="2" class="skydot"/>';
        }
      });
      s += dim + '<polyline class="hzn-line" points="' + pts.trim() + '"/>' + lit;
      var lblY = phi > 0 ? Y1 - 6 : Y0 + 12;
      s += '<text class="hzn-lbl" x="' + (X0 + 8) + '" y="' + lblY + '">GROUND — below your horizon</text>';
      chartEl.innerHTML = s + "</svg>";
    }

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
      $("skp-list-title").textContent = "Visible " + MAG_NAME[mag].replace("to the ", "") +
        " · " + vis.length + (vis.length === 1 ? " star" : " stars");
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
    chartEl.addEventListener("mousemove", function (e) {
      var t = e.target.closest && e.target.closest(".skp-dot-vis");
      if (!t) { tipEl.style.display = "none"; return; }
      var h = hosts[+t.dataset.i];
      tipEl.innerHTML = "<b>" + h.name + "</b><br><span class='ct-dim'>" + starMeta(h) +
        "</span><br><span class='ct-dim'>click for its worlds</span>";
      tipEl.style.display = "block";
      tipEl.style.left = Math.min(e.clientX + 14, window.innerWidth - 260) + "px";
      tipEl.style.top = e.clientY + 14 + "px";
    });
    chartEl.addEventListener("mouseleave", function () { tipEl.style.display = "none"; });
    chartEl.addEventListener("click", function (e) {
      var svg = chartEl.querySelector("svg");
      if (!svg) return;
      // Click in SVG coords; collect every visible star within a small radius, so one click
      // on a crowded patch (the Kepler field) opens all of it.
      var pt = svg.createSVGPoint();
      pt.x = e.clientX; pt.y = e.clientY;
      var p = pt.matrixTransform(svg.getScreenCTM().inverse());
      // Pick radius ≈ 9 screen px in SVG units, so taps work on a phone-sized chart too.
      var R = Math.max(10, 9 * W / svg.getBoundingClientRect().width);
      selected = hosts.filter(function (h) {
        if (!h.vis) return false;
        var dx = xOf(h.ra) - p.x, dy = yOf(h.dec) - p.y;
        return dx * dx + dy * dy <= R * R;
      }).sort(function (a, b) { return a.vmag - b.vmag; });
      drawSpot();
      if (selected.length) $("skp-spot-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });

    $("skp-lat").addEventListener("input", function () {
      lat = +this.value;
      if (geoState === "ok") geoState = "";
      localStorage.setItem("skyLat", String(lat));
      updateGeoBtn();
      render();
    });
    document.querySelectorAll(".skp-mag-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        mag = b.dataset.mag;
        localStorage.setItem("skyMag", mag);
        selected = null;
        render();
      });
    });

    var geoBtn = $("skp-geo");
    if (!(navigator.geolocation && navigator.geolocation.getCurrentPosition)) geoBtn.hidden = true;
    function updateGeoBtn() {
      geoBtn.textContent =
        geoState === "busy" ? "… locating" :
        geoState === "ok" ? "◎ located · " + latLabel() :
        geoState === "err" ? "◎ no location — use the slider" : "◎ Use my location";
      geoBtn.classList.toggle("lit", geoState === "ok");
      geoBtn.disabled = geoState === "busy";
    }
    geoBtn.addEventListener("click", function () {
      if (geoState === "busy") return;
      geoState = "busy"; updateGeoBtn();
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          lat = Math.max(-65, Math.min(65, Math.round(pos.coords.latitude)));
          lon = pos.coords.longitude;
          localStorage.setItem("skyLat", String(lat));
          localStorage.setItem("skyLon", String(lon));
          geoState = "ok"; updateGeoBtn(); render();
        },
        function () { geoState = "err"; updateGeoBtn(); },
        { timeout: 12000, maximumAge: 600000 }
      );
    });
    updateGeoBtn();
  };
})();
