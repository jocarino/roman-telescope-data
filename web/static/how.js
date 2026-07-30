/* Animated explainers for "How we get the colours".
 *
 * These animations are meant to TEACH, not to decorate: each one performs the step its panel
 * describes, on the numbers actually drawn in the diagram, and shows the result as it goes.
 *   step 1  a trace walks the spectrum; the readout names the wavelength it is passing and how
 *           much the planet reflects there, and the methane dips arrive as it reaches them
 *   measured  one packet of light walks the optical path — slit, grating, fan, CCD — and the
 *           counts curve builds from where the colours land
 *   step 2  a cursor crosses all three panels at once; A and S are read off the curves and
 *           multiplied, and the third curve IS that product, computed here rather than drawn
 *   step 3  the spectrum from step 2 is weighted by each colour-matching curve and the three
 *           running totals fill, ending on the colour they imply
 *   step 5  a cursor sweeps Roman's bands: outside them the light is simply not recorded, and
 *           the reconstruction at the end is built from the four numbers that survived
 *
 * Two consequences of "the diagram computes the answer" worth knowing:
 *   - The picture is enriched even when nothing moves. Building a scene leaves it at its FINAL
 *     frame, so the product curve, the X/Y/Z totals, the swatch and the four-band reconstruction
 *     are all present for a reader who never triggers an animation — including one who has asked
 *     for prefers-reduced-motion, who gets the extra information and none of the movement.
 *   - Nothing is ever hidden waiting for a trigger that might not come. With JavaScript off, the
 *     diagrams are the authored SVG, which is drawn to be correct on its own.
 *
 * The maths is deliberately shallow — these are sketched curves, not the pipeline's data — so
 * the CIE step labels its own hex as an idea rather than a result. What is honest is the
 * MECHANISM: every number on screen is read off the shape beside it.
 *
 * Kept out of app.js deliberately (see CLAUDE.md): that file is where parallel sessions collide.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  function mk(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function seg(t, a, b) { return clamp01((t - a) / (b - a)); } // progress across a time window
  function ease(p) { return p * p * (3 - 2 * p); }
  function q(svg, role) { return svg.querySelector('[data-role="' + role + '"]'); }
  function qa(svg, role) {
    return Array.prototype.slice.call(svg.querySelectorAll('[data-role="' + role + '"]'));
  }
  /* Opacity is set as a fraction of whatever the element already had, so fading a curve that
   * lives at .55 in the stylesheet ends at .55 and not at 1. */
  function fader(el) {
    var b = parseFloat(window.getComputedStyle(el).opacity);
    if (isNaN(b)) b = 1;
    return function (v) { el.style.opacity = v * b; };
  }
  function drawer(el) {
    var len = el.getTotalLength();
    return function (p) {
      el.style.strokeDasharray = len;
      el.style.strokeDashoffset = len * (1 - clamp01(p));
    };
  }
  // A path as points, and the y it holds at a given x. Every curve here is x-monotonic.
  function sampler(path, n) {
    var L = path.getTotalLength(), pts = [], i, p;
    for (i = 0; i <= n; i++) {
      p = path.getPointAtLength((L * i) / n);
      pts.push([p.x, p.y]);
    }
    return pts;
  }
  function yAt(pts, x) {
    var last = pts[pts.length - 1];
    if (x <= pts[0][0]) return pts[0][1];
    if (x >= last[0]) return last[1];
    for (var i = 1; i < pts.length; i++) {
      if (pts[i][0] >= x) {
        var a = pts[i - 1], b = pts[i], f = (x - a[0]) / (b[0] - a[0] || 1);
        return a[1] + (b[1] - a[1]) * f;
      }
    }
    return last[1];
  }
  function span(el) { var b = el.getBBox(); return [b.x, b.x + b.width]; }
  function boxOf(rect) {
    var x = +rect.getAttribute("x"), y = +rect.getAttribute("y");
    return {
      x0: x, x1: x + +rect.getAttribute("width"),
      yt: y, yb: y + +rect.getAttribute("height"),
    };
  }
  // The plot's axes and what they mean, declared on the <svg> as data-plot / data-nm.
  function plotOf(svg) {
    var pl = (svg.getAttribute("data-plot") || "0,1,1,0").split(",").map(Number);
    var nm = (svg.getAttribute("data-nm") || "380,780").split(",").map(Number);
    return {
      x0: pl[0], x1: pl[1], yb: pl[2], yt: pl[3], nm0: nm[0], nm1: nm[1],
      xOf: function (l) { return this.x0 + ((l - this.nm0) / (this.nm1 - this.nm0)) * (this.x1 - this.x0); },
      nmOf: function (x) { return this.nm0 + ((x - this.x0) / (this.x1 - this.x0)) * (this.nm1 - this.nm0); },
      vOf: function (y) { return (this.yb - y) / (this.yb - this.yt); },
      yOf: function (v) { return this.yb - v * (this.yb - this.yt); },
    };
  }
  function pathFrom(points) {
    return points.map(function (p, i) {
      return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1);
    }).join(" ");
  }
  /* XYZ -> sRGB hex: the standard D65 matrix and gamma encode, the inverse of the sRGB -> Lab
   * conversion in app.js. Luminance is pinned to the site's swatch convention (Y = 0.60) so a
   * dim planet colour reads as a colour rather than as black. */
  function xyzHex(X, Y, Z) {
    var k = Y > 1e-6 ? 0.6 / Y : 0;
    X *= k; Y *= k; Z *= k;
    var lin = [
      3.2406 * X - 1.5372 * Y - 0.4986 * Z,
      -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
      0.0557 * X - 0.204 * Y + 1.057 * Z,
    ];
    return "#" + lin.map(function (c) {
      c = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(Math.max(c, 0), 1 / 2.4) - 0.055;
      var v = Math.round(clamp01(c) * 255).toString(16);
      return v.length < 2 ? "0" + v : v;
    }).join("");
  }

  /* The reflected-light spectrum computed by step 2, so step 3 weights the very curve the page
   * has just built rather than a fresh invention. Null until the step-2 scene is built (document
   * order guarantees it is, before step 3). */
  var PRODUCT = null;

  var SCENES = {
    /* ---- STEP 1: chemistry sculpts the curve ---------------------------------------- */
    archetypes: function (svg) {
      var P = plotOf(svg);
      var cloudy = q(svg, "cloudy"), label = q(svg, "cloudy-label");
      var curve = q(svg, "curve"), ch4 = q(svg, "ch4");
      var dips = qa(svg, "dip");
      var pts = sampler(curve, 140);
      var fCloudy = fader(cloudy), fLabel = fader(label), fCh4 = fader(ch4);
      var dipF = dips.map(fader);
      var drawCurve = drawer(curve);
      var cur = mk("line", { class: "dg-cur", x1: 40, y1: 20, x2: 40, y2: 158 }, svg);
      var dot = mk("circle", { class: "dg-dot", r: 3.2, cx: 40, cy: 62 }, svg);
      var rd = mk("text", { class: "rd", x: 536, y: 32, "text-anchor": "end" }, svg);
      var fCur = fader(cur), fDot = fader(dot);
      var T = { walk: [820, 2650] };

      return {
        dur: 3000,
        frame: function (t) {
          fCloudy(seg(t, 0, 520));
          fLabel(seg(t, 380, 820));
          var p = ease(seg(t, T.walk[0], T.walk[1]));
          drawCurve(p);
          var x = P.x0 + p * (P.x1 - P.x0), y = yAt(pts, x), nm = P.nmOf(x);
          var live = t > T.walk[0] && t < T.walk[1] + 100;
          fCur(live ? 1 : 0); fDot(live ? 1 : 0);
          cur.setAttribute("x1", x); cur.setAttribute("x2", x); cur.setAttribute("y1", y);
          dot.setAttribute("cx", x); dot.setAttribute("cy", y);
          dips.forEach(function (d, i) { dipF[i](x >= +d.getAttribute("x1") ? 1 : 0); });
          fCh4(seg(t, 2450, 2850));
          var band = dips.filter(function (d) {
            return Math.abs(nm - +d.getAttribute("data-band-nm")) < 16;
          })[0];
          rd.textContent = live
            ? Math.round(nm) + " nm · reflects " + P.vOf(y).toFixed(2) +
              (band ? " · CH₄ absorbs" : "")
            : t >= T.walk[1] ? "methane bites twice: 619 and 727 nm" : "";
        },
      };
    },

    /* ---- MEASURED: one packet of light down the optical path ------------------------ */
    spectrograph: function (svg) {
      var beam = q(svg, "beam"), slit = q(svg, "slit"), grating = q(svg, "grating");
      var rays = qa(svg, "ray"), counts = q(svg, "counts"), box = boxOf(q(svg, "box-counts"));
      var drawBeam = drawer(beam), drawGrating = drawer(grating), drawCounts = drawer(counts);
      var rayGeom = rays.map(function (r) {
        return {
          x1: +r.getAttribute("x1"), y1: +r.getAttribute("y1"),
          x2: +r.getAttribute("x2"), y2: +r.getAttribute("y2"),
          nm: +r.getAttribute("data-band-nm"), colour: r.getAttribute("stroke"),
          draw: drawer(r), fade: fader(r),
        };
      });
      var cPts = sampler(counts, 60), cSpan = span(counts);
      var photon = mk("circle", { class: "dg-dot", r: 3.4, cx: 8, cy: 82 }, svg);
      var fPhoton = fader(photon);
      // One dot per ray, and the tick each one leaves behind at its own wavelength.
      var landed = rayGeom.map(function (g) {
        var x = cSpan[0] + ((g.nm - 380) / 400) * (cSpan[1] - cSpan[0]);
        return {
          g: g,
          dot: mk("circle", { r: 3, cx: g.x1, cy: g.y1, fill: g.colour, opacity: 0 }, svg),
          tick: mk("line", { x1: x, y1: box.yb - 6, x2: x, y2: yAt(cPts, x), stroke: g.colour,
            "stroke-width": 1.5, opacity: 0 }, svg),
        };
      });
      // Right-anchored: these captions change length as the light moves, and a left-anchored
      // one runs off the edge of the viewBox on the longest of them.
      var stage = mk("text", { class: "rd", x: 548, y: 24, "text-anchor": "end" }, svg);
      var fSlit = fader(slit);
      var T = { inn: [0, 620], slit: [620, 900], grate: [900, 1350], fan: [1350, 2150],
        ticks: [2150, 2650], curve: [2500, 3400] };

      return {
        dur: 3600,
        frame: function (t) {
          drawBeam(seg(t, T.inn[0], T.inn[1]));
          fSlit(t > T.slit[0] - 200 ? 1 : 0.35);
          drawGrating(seg(t, T.grate[0], T.grate[1]));
          // The packet: in along the beam, held at the slit, on to the grating.
          var px = 8;
          if (t < T.slit[0]) px = 8 + ease(seg(t, T.inn[0], T.inn[1])) * 112;
          else if (t < T.grate[1]) px = 120 + ease(seg(t, T.slit[1], T.grate[1])) * 62;
          photon.setAttribute("cx", px);
          fPhoton(t < T.grate[1] ? 1 : 0);
          var fanP = ease(seg(t, T.fan[0], T.fan[1]));
          landed.forEach(function (L, i) {
            L.g.draw(fanP);
            L.dot.setAttribute("cx", L.g.x1 + (L.g.x2 - L.g.x1) * fanP);
            L.dot.setAttribute("cy", L.g.y1 + (L.g.y2 - L.g.y1) * fanP);
            L.dot.style.opacity = fanP > 0 && fanP < 1 ? 1 : 0;
            L.tick.style.opacity = seg(t, T.ticks[0] + i * 120, T.ticks[0] + i * 120 + 260);
          });
          drawCounts(ease(seg(t, T.curve[0], T.curve[1])));
          stage.textContent =
            t < T.slit[0] ? "light in" :
            t < T.grate[1] ? "through the slit" :
            t < T.fan[1] ? "the grating fans it out: one angle per colour" :
            t < T.curve[1] ? "each colour lands on its own pixel" :
            "one exposure · every wavelength at once";
        },
      };
    },

    /* ---- STEP 2: the multiplication, done rather than drawn -------------------------- */
    multiply: function (svg) {
      var a = q(svg, "a"), s = q(svg, "s"), f = q(svg, "f");
      var BA = boxOf(q(svg, "box-a")), BS = boxOf(q(svg, "box-s")), BF = boxOf(q(svg, "box-f"));
      var pa = sampler(a, 90), ps = sampler(s, 90);
      var sa = span(a), ss = span(s), sf = span(f);
      var N = 60, samples = [], i, max = 0;
      for (i = 0; i <= N; i++) {
        var u = i / N;
        var va = (BA.yb - yAt(pa, sa[0] + u * (sa[1] - sa[0]))) / (BA.yb - BA.yt);
        var vs = (BS.yb - yAt(ps, ss[0] + u * (ss[1] - ss[0]))) / (BS.yb - BS.yt);
        samples.push([va, vs, va * vs]);
        if (va * vs > max) max = va * vs;
      }
      /* The third panel is REPLACED by the product of the first two. It was hand-drawn before,
       * which is a fine sketch and a poor claim: this panel is the whole point of the step.
       * Scaled to fill its box, because only the shape carries the colour — the pipeline
       * normalises here too, and pins brightness separately (step 3). */
      f.setAttribute("d", pathFrom(samples.map(function (v, j) {
        return [sf[0] + (j / N) * (sf[1] - sf[0]), BF.yb - (v[2] / (max || 1)) * (BF.yb - BF.yt)];
      })));
      /* Interpolated, not nearest-sampled: step 3 reads this at a finer step than step 2 stores,
       * and rounding to the nearest stored sample there turns a smooth spectrum into a staircase. */
      PRODUCT = {
        at: function (u) {
          var f = clamp01(u) * N, i = Math.floor(f), frac = f - i;
          var a0 = samples[i][2], a1 = samples[Math.min(i + 1, N)][2];
          return (a0 + (a1 - a0) * frac) / (max || 1);
        },
      };

      var drawF = drawer(f);
      var curs = [BA, BS, BF].map(function (B) {
        return mk("line", { class: "dg-cur", x1: B.x0, y1: B.yt, x2: B.x0, y2: B.yb }, svg);
      });
      var fCurs = curs.map(fader);
      var rdA = mk("text", { class: "rd", x: BA.x0 + 10, y: 152 }, svg);
      var rdS = mk("text", { class: "rd", x: BS.x0 + 10, y: 152 }, svg);
      var rdF = mk("text", { class: "rd", x: BF.x0 + 10, y: 152 }, svg);
      var SWEEP = 2400;

      return {
        dur: 2700,
        frame: function (t) {
          var p = ease(seg(t, 0, SWEEP)), live = t < SWEEP;
          drawF(p);
          [[sa, 0], [ss, 1], [sf, 2]].forEach(function (pair) {
            var x = pair[0][0] + p * (pair[0][1] - pair[0][0]);
            curs[pair[1]].setAttribute("x1", x);
            curs[pair[1]].setAttribute("x2", x);
            fCurs[pair[1]](live ? 1 : 0);
          });
          var v = samples[Math.round(p * N)];
          rdA.textContent = live ? "A " + v[0].toFixed(2) : "";
          rdS.textContent = live ? "S " + v[1].toFixed(2) : "";
          rdF.textContent = live ? "= " + v[2].toFixed(2) : "= A × S at every λ";
        },
      };
    },

    /* ---- STEP 3: weight, sum, and land on a colour ----------------------------------- */
    cie: function (svg) {
      var P = plotOf(svg);
      var bars = [
        { role: "xbar", key: "X", y: 190 },
        { role: "ybar", key: "Y", y: 202 },
        { role: "zbar", key: "Z", y: 214 },
      ];
      bars.forEach(function (b) { b.pts = sampler(q(svg, b.role), 120); });

      // The spectrum being weighted is step 2's product; a flat one if that scene is absent.
      var spec = PRODUCT || { at: function () { return 0.6; } };
      var N = 120, steps = [], i, sums = { X: 0, Y: 0, Z: 0 }, norm = 0;
      for (i = 0; i <= N; i++) {
        var u = i / N, x = P.x0 + u * (P.x1 - P.x0), fv = spec.at(u);
        var row = { u: u, x: x, f: fv };
        bars.forEach(function (b) { row[b.key] = Math.max(0, P.vOf(yAt(b.pts, x))); });
        sums.X += fv * row.X; sums.Y += fv * row.Y; sums.Z += fv * row.Z;
        norm += row.Y;
        row.run = { X: sums.X, Y: sums.Y, Z: sums.Z };
        steps.push(row);
      }
      var total = { X: sums.X / norm, Y: sums.Y / norm, Z: sums.Z / norm };
      var peak = Math.max(total.X, total.Y, total.Z) || 1;
      var hex = xyzHex(total.X, total.Y, total.Z);

      /* The spectrum being weighted, drawn as a filled area rather than a fourth line: three
       * curves in this plot are already the eye's, and a fourth stroke in the same ink would
       * read as one of them instead of as the thing they are being applied to. */
      var ridge = steps.map(function (r) { return [r.x, P.yOf(r.f * 0.8)]; });
      var fPath = mk("path", { class: "dg-spec", "data-role": "spectrum",
        d: pathFrom([[P.x0, P.yb]].concat(ridge, [[P.x1, P.yb]])) + " Z" }, svg);
      svg.insertBefore(fPath, svg.firstChild); // behind the matching curves, never over them
      var fLabel = mk("text", { class: "rd", x: 536, y: 30, "text-anchor": "end" }, svg);
      fLabel.textContent = "F(λ) from step 2";
      var fSpec = fader(fPath), fLab = fader(fLabel);

      var cur = mk("line", { class: "dg-cur", x1: P.x0, y1: P.yt, x2: P.x0, y2: P.yb }, svg);
      var fCur = fader(cur);
      bars.forEach(function (b) {
        mk("text", { class: "rd", x: 46, y: b.y + 8 }, svg).textContent = b.key;
        mk("rect", { x: 60, y: b.y, width: 150, height: 8, fill: "none",
          stroke: "var(--line)" }, svg);
        b.fill = mk("rect", { class: "dg-bar-fill", x: 60, y: b.y, width: 0, height: 8 }, svg);
        b.val = mk("text", { class: "rd", x: 220, y: b.y + 8 }, svg);
      });
      var sw = mk("rect", { class: "dg-swatch", x: 474, y: 188, width: 36, height: 36,
        fill: hex }, svg);
      var swTxt = mk("text", { class: "rd", x: 380, y: 210 }, svg);
      var note = mk("text", { class: "rd rd-dim", x: 46, y: 228 }, svg);
      note.textContent = "sketched curves — the pipeline uses the tabulated CIE data";
      var fSw = fader(sw), fSwTxt = fader(swTxt), fNote = fader(note);
      var SWEEP = 2500;

      return {
        dur: 3200,
        frame: function (t) {
          fSpec(seg(t, 0, 500)); fLab(seg(t, 200, 700));
          var p = ease(seg(t, 700, 700 + SWEEP)), live = t > 700 && t < 700 + SWEEP;
          var row = steps[Math.round(p * N)];
          cur.setAttribute("x1", row.x); cur.setAttribute("x2", row.x);
          fCur(live ? 1 : 0);
          bars.forEach(function (b) {
            var run = row.run[b.key] / norm;
            b.fill.setAttribute("width", (150 * clamp01(run / peak)).toFixed(1));
            b.val.textContent = run.toFixed(2);
          });
          fSw(seg(t, 700 + SWEEP, 700 + SWEEP + 300));
          fSwTxt(seg(t, 700 + SWEEP, 700 + SWEEP + 300));
          fNote(seg(t, 700 + SWEEP, 700 + SWEEP + 300));
          swTxt.textContent = "three numbers → " + hex;
        },
      };
    },

    /* ---- STEP 5: what four filters keep, and what they never see --------------------- */
    bands: function (svg) {
      var P = plotOf(svg);
      var spectrum = q(svg, "spectrum"), pts = sampler(spectrum, 120);
      var bands = qa(svg, "band").map(function (r) {
        var x = +r.getAttribute("x"), w = +r.getAttribute("width");
        var centre = P.nmOf(x + w / 2);
        return {
          el: r, fade: fader(r), nm0: P.nmOf(x), nm1: P.nmOf(x + w),
          centre: centre, cx: x + w / 2, cy: yAt(pts, x + w / 2),
          label: r.getAttribute("data-band-nm"),
        };
      });
      bands.forEach(function (b) {
        b.dot = mk("circle", { class: "dg-dot", r: 3.4, cx: b.cx, cy: b.cy }, svg);
        b.fdot = fader(b.dot);
      });
      /* What Roman can rebuild: the four samples joined up, held flat below the first band
       * because nothing was measured there — the reconstruction never invents a slope. */
      var recon = mk("path", { class: "dg-recon", d: pathFrom(
        [[P.x0, bands[0].cy]].concat(bands.map(function (b) { return [b.cx, b.cy]; }),
          [[P.x1, bands[bands.length - 1].cy]])) }, svg);
      var fRecon = fader(recon);
      var cur = mk("line", { class: "dg-cur", x1: P.x0, y1: P.yt, x2: P.x0, y2: P.yb }, svg);
      var fCur = fader(cur);
      var rd = mk("text", { class: "rd", x: 40, y: 180 }, svg);
      var SWEEP = 2300;

      return {
        dur: 3200,
        frame: function (t) {
          var p = seg(t, 0, SWEEP), live = t < SWEEP;
          var x = P.x0 + p * (P.x1 - P.x0), nm = P.nmOf(x);
          cur.setAttribute("x1", x); cur.setAttribute("x2", x);
          fCur(live ? 1 : 0);
          var inside = null;
          bands.forEach(function (b) {
            var on = nm >= b.nm0 && nm <= b.nm1;
            if (on) inside = b;
            b.fade(live && on ? 2.4 : 1);
            b.fdot(!live || nm > b.centre ? 1 : 0);
          });
          fRecon(seg(t, SWEEP + 100, SWEEP + 700));
          rd.textContent = live
            ? Math.round(nm) + " nm · " + (inside
                ? "band " + inside.label + " is measuring"
                : "no filter here — this light is never recorded")
            : "four numbers survive · below the first band, held flat rather than guessed";
        },
      };
    },
  };

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var page = document.querySelector(".how");
    if (!page) return;
    var diagrams = Array.prototype.slice.call(page.querySelectorAll(".dg[data-teach]"));
    if (!diagrams.length) return;

    var scenes = [];
    diagrams.forEach(function (svg) {
      var build = SCENES[svg.getAttribute("data-teach")];
      if (!build) return;
      var scene;
      try {
        scene = build(svg);
      } catch (e) {
        return; // a scene that cannot measure its own diagram simply does not animate
      }
      scene.svg = svg;
      scene.frame(scene.dur); // at rest = the finished picture, extra findings included
      scenes.push(scene);
    });
    if (!scenes.length) return;

    var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (still) return; // enriched, motionless, and no play control to promise otherwise

    scenes.forEach(function (scene) {
      var raf = 0, t0 = null;
      scene.play = function () {
        cancelAnimationFrame(raf);
        /* A hidden tab paints no frames, so starting here would run frame 0 — the empty one —
         * and then stall there for as long as the tab stays in the background. Nobody is
         * watching, so there is nothing to animate: leave the finished picture up. */
        if (document.hidden) { scene.frame(scene.dur); return; }
        t0 = null; // null, not 0: a frame timestamp of 0 is a valid start, and !0 is not
        var step = function (now) {
          if (t0 === null) t0 = now;
          var t = now - t0;
          scene.frame(Math.min(t, scene.dur));
          if (t < scene.dur) raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
      };
      var bar = document.createElement("div");
      bar.className = "dg-bar";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dg-replay";
      btn.textContent = "▷ PLAY";
      btn.setAttribute("aria-label", "Play this diagram's animation");
      btn.addEventListener("click", scene.play);
      bar.appendChild(btn);
      scene.svg.parentNode.insertBefore(bar, scene.svg.nextSibling);
    });

    // First sight of a diagram plays it; after that the button is the only trigger, so a slow
    // scroll back up never restarts something the reader is already reading.
    if (!("IntersectionObserver" in window)) return;
    var seen = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var scene = scenes.filter(function (s) { return s.svg === entry.target; })[0];
          if (scene) scene.play();
          seen.unobserve(entry.target);
        });
      },
      { threshold: 0.4 }
    );
    scenes.forEach(function (s) { seen.observe(s.svg); });

    /* The chain at the top of the page (PLANET × STAR → EYE → #hex) is the whole pipeline in
     * one line, so it lights up in signal order on load rather than waiting to be scrolled to. */
    var chain = page.querySelector(".how-chain");
    if (chain) {
      Array.prototype.forEach.call(chain.children, function (node, i) {
        node.style.setProperty("--i", i);
      });
      chain.classList.add("how-chain-live");
    }
  });
})();
