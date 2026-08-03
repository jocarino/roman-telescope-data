// Colour census: the whole catalog as one dataset. Three canvas charts over the same
// fetched gallery index (hue strip, temperature x brightness scatter, Roman dE histogram).
// Plain JS, no chart lib; page-scoped (only census.html loads this file).
(function () {
  "use strict";

  var TIP, PLANETS = [];

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  var FONT = '10px ui-monospace, "SF Mono", Menlo, Consolas, monospace';

  function hexToRgb(hex) {
    var h = hex.replace("#", "");
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function hsl(hex) {
    var rgb = hexToRgb(hex), r = rgb[0] / 255, g = rgb[1] / 255, b = rgb[2] / 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    var l = (max + min) / 2;
    var s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    var h = 0;
    if (d > 0) {
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h = (h * 60 + 360) % 360;
    }
    return { h: h, s: s, l: l };
  }

  // ── Shared tooltip ────────────────────────────────────────────────────────
  function showTip(evt, html) {
    TIP.innerHTML = html;
    TIP.style.display = "block";
    var pad = 14, w = TIP.offsetWidth, h = TIP.offsetHeight;
    var x = evt.clientX + pad, y = evt.clientY + pad;
    if (x + w > window.innerWidth - 8) x = evt.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = evt.clientY - h - pad;
    TIP.style.left = x + "px";
    TIP.style.top = y + "px";
  }
  function hideTip() { TIP.style.display = "none"; }
  function tipHtml(p, extra) {
    return '<span class="ct-sw" style="background:' + p.hex + '"></span><b>' + p.name +
      "</b><br><span class=\"ct-dim\">" + p.hex + (extra ? " · " + extra : "") + "</span>";
  }

  // ── Canvas plumbing: size to container width, redraw on resize ───────────
  function chart(canvas, cssHeight, draw) {
    var state = { canvas: canvas, ctx: canvas.getContext("2d"), w: 0, h: 0 };
    function layout() {
      var w = canvas.parentElement.clientWidth;
      var h = typeof cssHeight === "function" ? cssHeight(w) : cssHeight;
      var dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      canvas.style.height = h + "px";
      state.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      state.w = w;
      state.h = h;
      draw(state);
    }
    layout();
    var t;
    window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(layout, 120); });
    state.redraw = function () { draw(state); };
    return state;
  }
  function clear(st) { st.ctx.clearRect(0, 0, st.w, st.h); }
  function go(p) { window.location.href = "/planet/" + p.id; }  // extensionless: the canonical form

  // ── 1 · Hue strip ────────────────────────────────────────────────────────
  function stripChart(canvas) {
    var order = PLANETS.slice().sort(function (a, b) {
      var A = hsl(a.hex), B = hsl(b.hex);
      var an = A.s < 0.09, bn = B.s < 0.09;  // near-neutrals grouped at the right end
      if (an !== bn) return an ? 1 : -1;
      return an ? A.l - B.l : (A.h - B.h) || (A.l - B.l);
    });
    var hover = -1;

    var st = chart(canvas, 110, function (s) {
      clear(s);
      var n = order.length, top = 8, hgt = s.h - 26;
      for (var i = 0; i < n; i++) {
        var x0 = Math.floor((i / n) * s.w), x1 = Math.floor(((i + 1) / n) * s.w);
        s.ctx.fillStyle = order[i].hex;
        s.ctx.fillRect(x0, top, Math.max(1, x1 - x0), hgt);
      }
      if (hover >= 0) {
        var hx = Math.floor(((hover + 0.5) / n) * s.w);
        s.ctx.fillStyle = "#fff";
        s.ctx.fillRect(hx - 1, 0, 2, top + hgt + 4);
      }
      s.ctx.fillStyle = cssVar("--fg-dim");
      s.ctx.font = FONT;
      s.ctx.textAlign = "left";
      s.ctx.fillText(order.length + " planets, sorted by hue", 0, s.h - 4);
    });

    function pick(evt) {
      var r = canvas.getBoundingClientRect();
      var i = Math.floor(((evt.clientX - r.left) / r.width) * order.length);
      return i >= 0 && i < order.length ? i : -1;
    }
    canvas.addEventListener("mousemove", function (evt) {
      var i = pick(evt);
      if (i !== hover) { hover = i; st.redraw(); }
      if (i >= 0) showTip(evt, tipHtml(order[i]));
    });
    canvas.addEventListener("mouseleave", function () { hover = -1; st.redraw(); hideTip(); });
    canvas.addEventListener("click", function (evt) {
      var i = pick(evt);
      if (i >= 0) go(order[i]);
    });
  }

  // ── 2 · Temperature x brightness scatter ─────────────────────────────────
  function scatterChart(canvas) {
    var pts = PLANETS.filter(function (p) { return p.temp > 0 && p.lum != null; });
    var tMin = 40, tMax = 4600, lMax = 0;
    pts.forEach(function (p) { lMax = Math.max(lMax, p.lum); });
    lMax = Math.min(1, lMax * 1.12);
    var M = { l: 46, r: 10, t: 12, b: 34 };
    var hover = null, placed = [];

    function xOf(temp, s) {
      var f = (Math.log(Math.min(tMax, Math.max(tMin, temp))) - Math.log(tMin)) /
        (Math.log(tMax) - Math.log(tMin));
      return M.l + f * (s.w - M.l - M.r);
    }
    function yOf(lum, s) {
      var f = Math.sqrt(lum / lMax);
      return s.h - M.b - f * (s.h - M.t - M.b);
    }

    var st = chart(canvas, function (w) { return w < 560 ? 330 : 430; }, function (s) {
      clear(s);
      var ctx = s.ctx, line = cssVar("--line"), dim = cssVar("--fg-dim");
      ctx.font = FONT;
      // Recessive grid + axis labels (plain-English on both axes).
      ctx.strokeStyle = line;
      ctx.fillStyle = dim;
      ctx.lineWidth = 1;
      [50, 100, 300, 1000, 3000].forEach(function (t) {
        var x = Math.round(xOf(t, s)) + 0.5;
        ctx.globalAlpha = 0.45;
        ctx.beginPath(); ctx.moveTo(x, M.t); ctx.lineTo(x, s.h - M.b); ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.textAlign = "center";
        ctx.fillText(t + " K", x, s.h - M.b + 14);
      });
      [0.05, 0.2, 0.5].forEach(function (l) {
        if (l > lMax) return;
        var y = Math.round(yOf(l, s)) + 0.5;
        ctx.globalAlpha = 0.45;
        ctx.beginPath(); ctx.moveTo(M.l, y); ctx.lineTo(s.w - M.r, y); ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.textAlign = "right";
        ctx.fillText(Math.round(l * 100) + "%", M.l - 6, y + 3);
      });
      ctx.textAlign = "left";
      ctx.fillText("↑ reflects more light", M.l + 4, M.t + 2);
      ctx.textAlign = "center";
      ctx.fillText("colder ← planet temperature → hotter", (M.l + s.w - M.r) / 2, s.h - 4);
      // Dots: each planet as a 3px pixel in its own colour (the datum IS the colour).
      placed = [];
      pts.forEach(function (p) {
        var x = xOf(p.temp, s), y = yOf(p.lum, s);
        ctx.fillStyle = p.hex;
        ctx.fillRect(Math.round(x) - 1.5, Math.round(y) - 1.5, 3, 3);
        placed.push({ x: x, y: y, p: p });
      });
      if (hover) {
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 1;
        ctx.strokeRect(Math.round(hover.x) - 4.5, Math.round(hover.y) - 4.5, 9, 9);
      }
    });

    function pick(evt) {
      var r = canvas.getBoundingClientRect();
      var mx = evt.clientX - r.left, my = evt.clientY - r.top;
      var best = null, bd = 12 * 12;
      for (var i = 0; i < placed.length; i++) {
        var dx = placed[i].x - mx, dy = placed[i].y - my, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = placed[i]; }
      }
      return best;
    }
    canvas.addEventListener("mousemove", function (evt) {
      var b = pick(evt);
      if (b !== hover) { hover = b; st.redraw(); }
      if (b) {
        showTip(evt, tipHtml(b.p, Math.round(b.p.temp) + " K · reflects " +
          Math.round(b.p.lum * 100) + "%"));
      } else hideTip();
    });
    canvas.addEventListener("mouseleave", function () { hover = null; st.redraw(); hideTip(); });
    canvas.addEventListener("click", function (evt) {
      var b = pick(evt);
      if (b) go(b.p);
    });
  }

  // ── 3 · Roman dE histogram ───────────────────────────────────────────────
  function deChart(canvas) {
    var des = PLANETS.map(function (p) { return p.de; }).filter(function (v) {
      return v != null;
    }).sort(function (a, b) { return a - b; });
    var median = des[Math.floor(des.length / 2)] || 0;
    var BIN = 2.5, maxDe = Math.min(60, des[des.length - 1] || 0);
    var nBins = Math.max(1, Math.ceil(maxDe / BIN));
    var bins = new Array(nBins).fill(0);
    des.forEach(function (v) { bins[Math.min(nBins - 1, Math.floor(v / BIN))]++; });
    var peak = Math.max.apply(null, bins);
    var M = { l: 10, r: 10, t: 18, b: 34 };
    var hover = -1;

    var st = chart(canvas, 240, function (s) {
      clear(s);
      var ctx = s.ctx, accent = cssVar("--accent"), dim = cssVar("--fg-dim");
      ctx.font = FONT;
      var plotW = s.w - M.l - M.r, plotH = s.h - M.t - M.b;
      var bw = plotW / nBins;
      for (var i = 0; i < nBins; i++) {
        var h = bins[i] === 0 ? 0 : Math.max(2, (bins[i] / peak) * plotH);
        var x = M.l + i * bw;
        ctx.fillStyle = accent;
        ctx.globalAlpha = hover === i ? 1 : 0.75;
        ctx.fillRect(Math.round(x) + 1, s.h - M.b - h, Math.max(1, Math.floor(bw) - 2), h);
      }
      ctx.globalAlpha = 1;
      ctx.fillStyle = dim;
      ctx.strokeStyle = dim;
      for (var t = 0; t <= maxDe; t += 10) {
        var tx = Math.round(M.l + (t / (nBins * BIN)) * plotW) + 0.5;
        ctx.textAlign = "center";
        ctx.fillText("ΔE " + t, tx, s.h - M.b + 14);
      }
      // Median marker, direct-labeled.
      var mx = Math.round(M.l + (median / (nBins * BIN)) * plotW) + 0.5;
      ctx.strokeStyle = "#fff";
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(mx, M.t - 4); ctx.lineTo(mx, s.h - M.b); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#fff";
      ctx.textAlign = mx > s.w / 2 ? "right" : "left";
      ctx.fillText("median ΔE " + median.toFixed(1), mx + (mx > s.w / 2 ? -6 : 6), M.t + 4);
      ctx.fillStyle = dim;
      ctx.textAlign = "center";
      ctx.fillText("0 = Roman sees the identical colour · higher = more colour identity lost",
        s.w / 2, s.h - 4);
    });

    canvas.addEventListener("mousemove", function (evt) {
      var r = canvas.getBoundingClientRect();
      var plotW = r.width - M.l - M.r;
      var i = Math.floor(((evt.clientX - r.left - M.l) / plotW) * nBins);
      i = i >= 0 && i < nBins ? i : -1;
      if (i !== hover) { hover = i; st.redraw(); }
      if (i >= 0) {
        showTip(evt, "<b>" + bins[i] + " planet" + (bins[i] === 1 ? "" : "s") + "</b><br>" +
          '<span class="ct-dim">ΔE ' + (i * BIN).toFixed(1) + "–" +
          ((i + 1) * BIN).toFixed(1) + "</span>");
      } else hideTip();
    });
    canvas.addEventListener("mouseleave", function () { hover = -1; st.redraw(); hideTip(); });
  }

  // ── Stat tiles ───────────────────────────────────────────────────────────
  function stats(mount) {
    var fams = {};
    PLANETS.forEach(function (p) { fams[p.family] = 1; });
    var des = PLANETS.map(function (p) { return p.de; }).sort(function (a, b) { return a - b; });
    var median = des[Math.floor(des.length / 2)] || 0;
    function tile(v, l) { return '<span class="cs-tile"><b>' + v + "</b>" + l + "</span>"; }
    // Jargon in the tiles gets the same hover mark as everywhere else (glossary.js).
    function g(id, text) { return window.glossHTML ? window.glossHTML(id, text) : text; }
    mount.innerHTML =
      tile(PLANETS.length, "planets " + g("modelled")) +
      tile(Object.keys(fams).length, g("colour-family", "colour families")) +
      tile(g("delta-e2000", "ΔE") + " " + median.toFixed(1), "median Roman colour error");
  }

  window.censusInit = function (cfg) {
    TIP = document.getElementById("census-tip");
    fetch(cfg.indexUrl).then(function (r) { return r.json(); }).then(function (rows) {
      PLANETS = rows;
      stats(document.getElementById("census-stats"));
      stripChart(document.getElementById("census-strip"));
      scatterChart(document.getElementById("census-scatter"));
      deChart(document.getElementById("census-de"));
    });
  };
})();
