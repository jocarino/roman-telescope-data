// Procedural planet renderer. One shared offscreen WebGL context renders an analytic lit
// sphere (bands, haze, limb-darkening, terminator) from a planet's palette + attributes, then
// blits into any target canvas. Three styles: "smooth", "retro" (pixel), "modern" (pixel).
//
// Two fidelity modes (opts.fidelity):
//   "classic"  (default) — bands are a single derived hue at varying lightness; physics-honest.
//   "stylised"           — belts/zones split into warm/cool tints, higher band gain, and FBM
//                          turbulence for mottled cloud edges. Prettier, NOT truer.
// Either way the swatch/palette/export are the physics-derived colours; stylised only restyles
// how this 3D render *interprets* that palette. The base hue and luminance are unchanged.
//
// Honest by construction: colour comes from the derived palette; texture (bands) is schematic.
//
// EXCEPT for the five solar-system anchors, which can also be drawn from a REAL map
// (opts.map — see web/textures.py). There the light-and-dark pattern is a real spacecraft
// map sampled on the same lit sphere, rescaled per channel by opts.mapGain so the map's own
// average is the planet's physics-derived colour. Morphology real, colour still computed.
// Saturn additionally gets its rings (opts.ring), which shrink the globe to make room.
// No external library, no build step.
(function () {
  "use strict";

  var VERT = "attribute vec2 p; varying vec2 v; void main(){ v = p; gl_Position = vec4(p,0.,1.); }";

  var FRAG = [
    "precision highp float;",
    "varying vec2 v;",
    "uniform vec3 pal[5];",
    "uniform float bandFreq, bandContrast, haze, brightness, light, dither, levels, rot;",
    "uniform float turb, warmCool, bandGain;",  // stylised-mode restyling (0 in classic)
    "uniform float phase;",  // orbital phase angle in radians: 0 = fully lit, pi = backlit
    "uniform int pixel, outline;",
    // Real-map mode (the five solar-system anchors only; useMap = 0 everywhere else).
    // mapGain = derived colour / the map's own mean, so the rescaled map averages to the
    // planet's computed hex. sphereScale shrinks the globe within the canvas to leave room
    // for rings; it is 1.0 whenever there are none.
    "uniform sampler2D bodyMap, ringMap;",
    "uniform int useMap, useRing;",
    "uniform vec3 mapGain;",
    "uniform float mapExpo, sphereScale, aspect, ringInner, ringOuter, ringTilt, ringExpo;",
    "vec3 ramp(float t){",
    "  t = clamp(t,0.,1.)*4.;",
    "  vec3 c = pal[0];",
    "  c = mix(c, pal[1], clamp(t-0.,0.,1.));",
    "  c = mix(c, pal[2], clamp(t-1.,0.,1.));",
    "  c = mix(c, pal[3], clamp(t-2.,0.,1.));",
    "  c = mix(c, pal[4], clamp(t-3.,0.,1.));",
    "  return c;",
    "}",
    // 4x4 Bayer ordered dither
    "float bayer(vec2 fc){",
    "  int x = int(mod(fc.x,4.)); int y = int(mod(fc.y,4.));",
    "  int i = x + y*4;",
    "  float m[16];",
    "  m[0]=0.;m[1]=8.;m[2]=2.;m[3]=10.;m[4]=12.;m[5]=4.;m[6]=14.;m[7]=6.;",
    "  m[8]=3.;m[9]=11.;m[10]=1.;m[11]=9.;m[12]=15.;m[13]=7.;m[14]=13.;m[15]=5.;",
    "  float r=0.;",
    "  for(int k=0;k<16;k++){ if(k==i) r=m[k]; }",
    "  return r/16.0 - 0.5;",
    "}",
    // Value-noise FBM for stylised cloud turbulence (belt-edge warp + tone mottle).
    "float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }",
    "float vnoise(vec2 p){",
    "  vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);",
    "  float a=hash(i), b=hash(i+vec2(1.,0.)), c=hash(i+vec2(0.,1.)), d=hash(i+vec2(1.,1.));",
    "  return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);",
    "}",
    "float fbm(vec2 p){",
    "  float s=0.0, a=0.5;",
    "  for(int k=0;k<4;k++){ s += a*vnoise(p); p*=2.0; a*=0.5; }",
    "  return s;",
    "}",
    // How much of the ring system stands between a point on the globe and the star — the
    // dark band the rings paint across Saturn. Walk from the surface point towards the lamp,
    // find where that line crosses the ring plane, and read the rings' opacity at that radius.
    "float ringShadow(vec3 P, vec3 Ldir){",
    "  vec3 n = vec3(0.0, cos(ringTilt), sin(ringTilt));",
    "  float dn = dot(Ldir, n);",
    "  if(abs(dn) < 0.0001){ return 1.0; }",
    "  float s = -dot(P, n) / dn;",
    "  if(s <= 0.0){ return 1.0; }",
    "  float rq = length(P + s*Ldir);",
    "  if(rq < ringInner || rq > ringOuter){ return 1.0; }",
    "  float a = texture2D(ringMap, vec2((rq-ringInner)/(ringOuter-ringInner), 0.5)).a;",
    "  return 1.0 - 0.72*a;",
    "}",
    // Roll the top end off instead of letting it clip flat. Rescaling a map to a brighter
    // derived colour pushes its highlights past 1.0 — Jupiter's zones, Earth's ice — and a
    // hard clamp turns them into featureless white that has lost the planet's tint entirely.
    // Above the knee the response compresses smoothly towards 1.0 instead, which costs a
    // couple of percent of the disc average and keeps the highlights coloured.
    "vec3 softClip(vec3 c){",
    "  float k = 0.78;",
    "  vec3 hi = max(c - k, 0.0) / (1.0 - k);",
    "  hi = hi / (1.0 + hi);",
    "  return min(c, k + (1.0 - k)*hi);",
    "}",
    // Posterize for the pixel styles. The schematic path quantises its scalar `tone` and only
    // then looks up the ramp, so its output is always five colours on the planet's own hue. A
    // sampled map has no such tone, and quantising the three channels independently wrecks the
    // colour — (0.72, 0.80, 0.80) snaps to a neutral (0.8, 0.8, 0.8) and pale worlds come out
    // grey. So quantise BRIGHTNESS only and carry the chroma through untouched: same posterised
    // steps, hue and saturation preserved. Scaling by the max channel also keeps it in gamut.
    "vec3 posterize(vec3 c){",
    "  c = clamp(c, 0.0, 1.0);",
    "  float y = max(max(c.r, c.g), c.b);",
    "  if(y < 0.002){ return c; }",
    "  float q = clamp(floor((y + bayer(gl_FragCoord.xy)*dither)*levels + 0.5)/levels, 0.0, 1.0);",
    "  return c * (q / y);",
    "}",
    "void main(){",
    // The globe lives in its own coordinates, where 1.0 is one planet radius. `aspect` widens
    // the box horizontally (a ring system is ~2.3 radii across but only ~1 radius tall, so in
    // a square canvas the globe would have to shrink to 44% and sit in a sea of nothing);
    // sphereScale then trades a little height for air above and below the rings.
    "  vec2 uv = vec2(v.x*aspect, v.y) / sphereScale;",
    "  float r2 = dot(uv,uv);",
    "  if(r2 > 1.0 && useRing == 0){ discard; }",
    "  float z = sqrt(max(1.0 - r2, 0.0));",
    "  vec3 N = vec3(uv, z);",
    "  float lat = asin(clamp(uv.y,-1.,1.));",
    // Two lighting modes. phase < 0 (no phase control, e.g. gallery cards): the classic
    // fixed soft day/night term. phase >= 0 (slider/cycle-driven): the light physically
    // orbits with the phase angle — 0 = frontal full moon, pi/2 = half (lit right),
    // pi = backlit/dark, 3pi/2 = half lit from the LEFT (the waxing side of a full lunar
    // cycle) — with a visibility boost at crescent angles, because a strictly
    // Lambert-shaded crescent reads as black at this size. `pe` is the effective
    // illumination phase (0..pi, side-agnostic) used for the night floor and the boost.
    // L is hoisted out of the branch because the rings need the same lamp: which face of the
    // annulus is lit, and where the globe's shadow falls across it.
    "  vec3 L = normalize(vec3(cos(light)*0.55, 0.28, 0.90));",
    "  float nightF = 0.34;",
    "  float lit;",
    "  float pe = 0.0;",
    "  float limb = pow(z, 0.30);",
    "  if(phase >= 0.0){",
    "    L = normalize(vec3(sin(phase), 0.25, cos(phase)));",
    "    pe = min(phase, 6.28319 - phase);",
    "    lit = smoothstep(-0.06, 0.34, dot(N, L));",
    "    lit = min(1.0, lit * (1.0 + 2.2*clamp((pe-1.4)*0.7, 0.0, 1.0)));",
    "    nightF = mix(0.20, 0.05, clamp(pe*0.55, 0.0, 1.0));",
    "  } else {",
    "    lit = smoothstep(-0.08, 0.42, dot(N, L));",
    "  }",
    "  float shade = (nightF + (1.0-nightF)*lit) * limb;",
    // Longitudinal swirl that scrolls with `rot` — makes rotation visible on banded worlds,
    // and doubles as the real map's longitude. atan(uv.x, z) is continuous everywhere on the
    // VISIBLE hemisphere (z >= 0), so a sampled map has no seam running down the globe: the
    // wrap happens out in texture space, where REPEAT handles it.
    "  float lon = atan(uv.x, z) + rot;",
    "  float rim = smoothstep(0.74,1.0,r2);",
    "  vec3 col = vec3(0.0);",
    "  float alpha = 0.0;",
    "  if(r2 <= 1.0){",
    "  if(useMap == 1){",
    // Real map: the pattern is measured, the colour is not. mapGain rescales every texel so
    // the map's own mean is the planet's derived hex — see web/textures.py.
    "    vec2 tc = vec2(lon*0.15915494 + 0.5, 0.5 - lat*0.31830989);",
    "    vec3 alb = texture2D(bodyMap, tc).rgb * mapGain;",
    "    float sh = shade * brightness * mapExpo;",
    "    if(useRing == 1){ sh *= ringShadow(N, L); }",
    "    col = softClip(max(alb * sh, 0.0));",
    "    if(pixel==1){ col = posterize(col); }",
    "  } else {",
    // Stylised: warp the belt phase and mottle the tone with turbulence (0 in classic).
    "    float wphase = 0.0, mottle = 0.0;",
    "    if(turb > 0.0){",
    "      wphase = (fbm(vec2(uv.x*2.2 + z*1.5, lat*3.0)) - 0.5) * turb * 1.6;",
    "      mottle = (fbm(vec2(uv.x*4.0 - z, lat*6.0 + 3.0)) - 0.5) * turb;",
    "    }",
    "    float band = 0.5 + 0.5*sin(lat*bandFreq + wphase + sin(lat*bandFreq*0.5)*0.6);",
    "    band = mix(0.5, band, bandContrast);",
    "    band += 0.12 * bandContrast * sin(lon*3.0 + lat*bandFreq*0.5);",
    "    float tone = shade * (0.60 + bandGain*band) * brightness + rim*haze*0.28;",
    "    tone *= 1.0 + mottle*0.12;",
    // Pixel styles: dither THEN posterize -> clean flat colour bands with dithered edges.
    "    if(pixel==1){",
    "      tone = clamp(tone, 0.0, 1.0);",
    "      tone += bayer(gl_FragCoord.xy) * dither;",
    "      tone = floor(tone*levels + 0.5) / levels;",
    "    }",
    "    col = ramp(tone);",
    // Stylised two-tone: nudge bright zones warm (tan) and dark belts cool (lavender) along
    // the blue<->orange axis. This is the belt/zone contrast the eye reads in artistic renders.
    "    if(warmCool > 0.0){",
    "      float belt = clamp((band - 0.5) * 2.0, -1.0, 1.0);",
    "      col.r += belt * warmCool * 0.09;",
    "      col.g -= belt * warmCool * 0.02;",
    "      col.b -= belt * warmCool * 0.09;",
    "      col = clamp(col, 0.0, 1.0);",
    "    }",
    "    if(pixel==0){ col = mix(col, pal[4], rim*haze*0.4); }",  // smooth-only haze tint
    "  }",
    // Retro outline ring — but at crescent phases (beyond ~70°) the lit sliver lives
    // exactly on this rim, so exempt lit pixels there; nearer full phase the classic
    // outline stays intact.
    "  if(outline==1 && r2>0.90){",
    "    float keepLit = clamp(lit, 0.0, 1.0) * clamp((min(phase, 6.28319-phase)-1.2)*1.2, 0.0, 1.0);",
    "    col *= mix(0.35, 0.9, keepLit);",
    "  }",
    "    alpha = 1.0;",
    "  }",
    // Rings: the view ray at this pixel meets the tilted ring plane at exactly one point, so
    // the annulus is one closed-form lookup — radius rr, depth zr. The half with zr < 0 runs
    // behind the globe and is simply not drawn there.
    "  if(useRing == 1){",
    "    float st = max(sin(ringTilt), 0.001);",
    "    float zr = -uv.y * cos(ringTilt) / st;",
    "    float rr = sqrt(uv.x*uv.x + (uv.y/st)*(uv.y/st));",
    "    bool hidden = (zr < 0.0) && (r2 <= 1.0);",
    "    if(rr >= ringInner && rr <= ringOuter && !hidden){",
    "      vec4 rc = texture2D(ringMap, vec2((rr-ringInner)/(ringOuter-ringInner), 0.5));",
    "      vec3 n = vec3(0.0, cos(ringTilt), sin(ringTilt));",
    // A flat annulus is lit by how square-on the lamp strikes its face; then the globe throws
    // its own shadow across the far arc.
    "      float face = 0.30 + 0.70*abs(dot(n, L));",
    "      vec3 P = vec3(uv.x, uv.y, zr);",
    "      float t = dot(P, L);",
    "      float d2 = dot(P - t*L, P - t*L);",
    "      float shadow = (t < 0.0 && d2 < 1.0) ? 0.26 : 1.0;",
    "      vec3 rcol = clamp(rc.rgb * ringExpo * face * shadow, 0.0, 1.0);",
    "      if(pixel==1){ rcol = posterize(rcol); }",
    // Straight-alpha "over": rings in front of the globe, or alone against the backdrop.
    "      float na = rc.a + alpha*(1.0 - rc.a);",
    "      col = (rcol*rc.a + col*alpha*(1.0 - rc.a)) / max(na, 0.0001);",
    "      alpha = na;",
    "    }",
    "  }",
    "  if(alpha < 0.02){ discard; }",
    "  gl_FragColor = vec4(col, alpha);",
    "}",
  ].join("\n");

  var gl, prog, glCanvas, U = {};

  function init() {
    if (gl) return true;
    glCanvas = document.createElement("canvas");
    gl = glCanvas.getContext("webgl", { premultipliedAlpha: false, antialias: false });
    if (!gl) return false;
    var vs = compile(gl.VERTEX_SHADER, VERT);
    var fs = compile(gl.FRAGMENT_SHADER, FRAG);
    prog = gl.createProgram();
    gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
    gl.useProgram(prog);
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    ["pal","bandFreq","bandContrast","haze","brightness","light","dither","levels","rot",
     "turb","warmCool","bandGain","phase","pixel","outline",
     "useMap","useRing","mapGain","mapExpo","sphereScale","aspect",
     "ringInner","ringOuter","ringTilt","ringExpo","bodyMap","ringMap"]
      .forEach(function (n) { U[n] = gl.getUniformLocation(prog, n === "pal" ? "pal[0]" : n); });
    // Fixed texture units: the body map on 0, the ring strip on 1. Never changes.
    gl.uniform1i(U.bodyMap, 0);
    gl.uniform1i(U.ringMap, 1);
    return true;
  }

  // ── Real maps ────────────────────────────────────────────────────────────────────────
  // Images load asynchronously, so render() draws the schematic globe until one arrives and
  // silently upgrades on a later frame. That is invisible on the hero (spin() repaints ~30
  // times a second) and correct everywhere else: never block a render waiting on a texture.
  var texCache = {};   // url -> { tex, ready }
  var texWaiters = [];

  function texture(url, repeatS) {
    var e = texCache[url];
    if (e) return e;
    e = texCache[url] = { tex: gl.createTexture(), ready: false };
    // A 1x1 mid-grey stands in until the image decodes, so sampling is always defined.
    gl.bindTexture(gl.TEXTURE_2D, e.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
      new Uint8Array([128, 128, 128, 255]));
    var img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = function () {
      gl.bindTexture(gl.TEXTURE_2D, e.tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      // Both maps are power-of-two, so mipmaps are available — and needed: the pixel styles
      // squeeze a 1024-wide map into an 80px globe, which aliases into noise without them.
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      // Longitude wraps (the map is a cylinder); latitude must not, or the poles bleed.
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, repeatS ? gl.REPEAT : gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      e.ready = true;
      texWaiters.forEach(function (cb) { cb(url); });
    };
    img.src = url;
    return e;
  }

  // Start fetching a planet's map before anyone asks to see it, so flipping the Source knob
  // is instant rather than a beat of schematic globe.
  function preload(map) {
    if (!map || !init()) return;
    texture(map.file, true);
    if (map.ring) texture(map.ring.file, false);
  }
  // Called with the url whenever a map finishes loading — for one-shot renders that would
  // otherwise never repaint.
  function onTexture(cb) { texWaiters.push(cb); }
  function compile(type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(s));
    return s;
  }

  function hexToRgb(h) {
    h = h.replace("#", "");
    return [parseInt(h.substr(0,2),16)/255, parseInt(h.substr(2,2),16)/255, parseInt(h.substr(4,2),16)/255];
  }

  // Derive shader params from planet attributes.
  function derive(opts) {
    var r = opts.radius || 8;
    var cls = r < 2 ? "rocky" : (r < 6 ? "ice" : "gas");
    var cloud = (opts.cloudState || "").toLowerCase();
    var cloudFree = cloud.indexOf("cloud-free") >= 0 || cloud.indexOf("free") >= 0;
    var bandFreq = cls === "gas" ? 15.0 : (cls === "ice" ? 7.0 : 2.5);
    var bandContrast = cls === "rocky" ? 0.25 : (cloudFree ? 0.25 : 0.8);
    var lum = opts.lumY == null ? 0.5 : opts.lumY;
    var brightness = 0.72 + Math.min(lum, 1) * 0.55;   // dark planets stay darker
    // The planet's OWN computed colour, not a ramp stop. This used to read palette[2], which
    // held the true colour back when the middle stop kept the base's lightness; the ramp is now
    // an evenly spaced design object whose middle stop is ~0.53 light, and reading it here made
    // every planet render darker and hazier (blueness below is an absolute channel gap, so the
    // same hue at lower lightness scores as far bluer). palette[2] stays as the fallback.
    var base = hexToRgb(opts.baseHex || opts.palette[2] || opts.palette[0]);
    var haze = Math.max(0, base[2] - Math.max(base[0], base[1])) * 2.2; // blueness -> haze
    return { bandFreq: bandFreq, bandContrast: bandContrast, brightness: brightness, haze: Math.min(haze, 1) };
  }

  // Exposure for the real-map path. The schematic path runs its tone through the 5-stop ramp,
  // which lifts everything into 0.18-0.88 lightness; a sampled map has no such ramp, so this
  // constant puts a mapped globe at the same on-screen brightness as the schematic one it
  // replaces. Tuned by eye against the five anchors, side by side.
  var MAP_EXPOSURE = 1.25;
  // Rings are far brighter than the strip's stored values, which assume a lit render.
  var RING_EXPOSURE = 2.0;
  // How much vertical room the ringed render reserves, in planet radii. The rings only reach
  // outer*sin(tilt) ~ 1.02 radii above and below the equator, so 1.10 is the globe at 91% of
  // the frame height with a little air — nothing like the 44% a square frame would force.
  var RING_VFIT = 1.10;
  var RING_HMARGIN = 1.03;

  // How wide a ringed planet's frame has to be, relative to its height. Snapped to eighths so
  // both render resolutions (80 and 480 px tall) stay whole pixels wide and the pixel styles
  // keep their integer CSS upscale.
  function ringAspect(ring) {
    if (!ring) return 1;
    return Math.round(((ring.outer * RING_HMARGIN) / RING_VFIT) * 8) / 8;
  }

  // Is this planet's map decoded and ready to draw? Anything not ready yet simply falls back
  // to the schematic globe — never stall a frame on a pending image.
  function mapReady(opts) {
    return !!(opts.map && texture(opts.map.file, true).ready);
  }

  // Bind the real map (and rings) for this draw, or switch the shader back to schematic bands.
  function setMap(opts) {
    var m = opts.map;
    var on = mapReady(opts);
    gl.uniform1i(U.useMap, on ? 1 : 0);
    if (!on) {
      gl.uniform1i(U.useRing, 0);
      gl.uniform1f(U.sphereScale, 1.0);
      return;
    }
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture(m.file, true).tex);
    // Per-channel rescale: derived colour / the map's own mean, so the map averages to the
    // planet's computed hex. Both sides are sRGB-encoded 0-255, the space this shader works
    // in, so the match holds for the colour as displayed. See tools/prep_textures.py.
    var t = hexToRgb(opts.baseHex || opts.palette[2] || opts.palette[0]);
    var mean = m.mean || [128, 128, 128];
    gl.uniform3f(U.mapGain,
      t[0] / Math.max(mean[0] / 255, 0.02),
      t[1] / Math.max(mean[1] / 255, 0.02),
      t[2] / Math.max(mean[2] / 255, 0.02));
    // The schematic path folds the planet's own luminance into `brightness`; keep that, since
    // a dark world should stay dark whichever way its surface is drawn.
    gl.uniform1f(U.mapExpo, MAP_EXPOSURE);

    var ring = m.ring && texture(m.ring.file, false);
    var ringOn = !!(ring && ring.ready);
    gl.uniform1i(U.useRing, ringOn ? 1 : 0);
    // How far the globe has to shrink for its rings to fit, in planet radii. The frame holds
    // 1/sphereScale radii vertically and aspect/sphereScale horizontally, so whichever of the
    // two runs out first sets the scale. In the wide hero frame that is the height, and the
    // globe barely shrinks; on a square gallery card it is the width, and Saturn pulls back to
    // ~43% — small, but a ringless Saturn is just a cream ball, so the rings are what earn
    // their space at card size.
    gl.uniform1f(U.sphereScale, ringOn
      ? 1 / Math.max(RING_VFIT, (m.ring.outer * RING_HMARGIN) / (opts.aspect || 1))
      : 1.0);
    if (!ringOn) return;
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, ring.tex);
    gl.uniform1f(U.ringInner, m.ring.inner);
    gl.uniform1f(U.ringOuter, m.ring.outer);
    gl.uniform1f(U.ringTilt, ((m.ring.tilt || 26.7) * Math.PI) / 180);
    gl.uniform1f(U.ringExpo, RING_EXPOSURE);
    gl.activeTexture(gl.TEXTURE0);
  }

  function render(target, opts) {
    if (!target || !opts || !opts.palette || !init()) return;
    var pixel = opts.style !== "smooth";
    var res = pixel ? 80 : 480;
    // Ringed planets render into a wide frame rather than a square one; `res` is always the
    // HEIGHT, so the globe comes out the same size as every other planet's.
    var aspect = opts.aspect || 1;
    var resW = Math.round(res * aspect);
    glCanvas.width = resW; glCanvas.height = res;
    gl.uniform1f(U.aspect, aspect);
    gl.viewport(0, 0, resW, res);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    var d = derive(opts);
    var flat = [];
    for (var i = 0; i < 5; i++) {
      var c = hexToRgb(opts.palette[i] || opts.palette[opts.palette.length - 1]);
      flat.push(c[0], c[1], c[2]);
    }
    // Stylised mode: restyle this render only (palette/luminance stay physics-derived).
    var aug = opts.fidelity === "stylised";
    gl.uniform3fv(U.pal, new Float32Array(flat));
    gl.uniform1f(U.bandFreq, d.bandFreq);
    gl.uniform1f(U.bandContrast, Math.min(1, d.bandContrast * (aug ? 1.2 : 1)));
    gl.uniform1f(U.haze, d.haze);
    gl.uniform1f(U.brightness, d.brightness);
    gl.uniform1f(U.turb, aug ? 1.0 : 0.0);
    gl.uniform1f(U.warmCool, aug ? 1.0 : 0.0);
    gl.uniform1f(U.bandGain, aug ? 0.66 : 0.44);
    gl.uniform1f(U.light, opts.light == null ? 0.0 : opts.light);
    gl.uniform1f(U.phase, opts.phase == null ? -1.0 : opts.phase);  // -1 = no phase control
    gl.uniform1i(U.pixel, pixel ? 1 : 0);
    // retro = fewer, bolder colour bands + outline; modern = more bands, no outline. Dither
    // amplitude is ~one posterization step so transitions read as clean pixel-art gradients.
    var levels = opts.style === "retro" ? 5.0 : 8.0;
    gl.uniform1f(U.levels, levels);
    // A full-amplitude dither is right for the schematic globe, whose tone is a smooth
    // gradient the dither breaks into pixel-art steps. A real map already varies pixel to
    // pixel, so the same amplitude reads as a dot screen laid over the geography — a third
    // of it keeps the banding smooth without burying Africa in noise.
    gl.uniform1f(U.dither, pixel ? (mapReady(opts) ? 0.3 : 0.9) / levels : 0.0);
    gl.uniform1i(U.outline, opts.style === "retro" ? 1 : 0);
    gl.uniform1f(U.rot, opts.rot || 0);
    setMap(opts);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    // Blit 1:1 into the target canvas; CSS does the INTEGER upscale (80->160 = 2x) with
    // image-rendering:pixelated, so pixels stay uniform and crisp (this was the jank).
    target.width = resW; target.height = res;
    var ctx = target.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(glCanvas, 0, 0);
  }

  // Radians added per ~33 ms frame — the single spin rate for every globe on the site.
  // Deliberately unhurried: at a third slower than it first shipped, a real map's features
  // stay readable as they cross the disc instead of streaming past.
  var SPIN_STEP = 0.033;

  // Rotation: a rAF loop that re-renders with an advancing `rot`. Throttled to ~30fps.
  // Only ever run for a few canvases at once (detail page + hovered card), so it's cheap.
  function spin(canvas, opts) {
    // Re-spinning an already-spinning canvas (e.g. the phase cycle re-issuing options)
    // carries the rotation over, so the globe keeps turning smoothly instead of jumping.
    var prev = canvas.__spin;
    stop(canvas);
    var st = { rot: prev ? prev.rot : Math.random() * 6.283, last: 0 };
    function frame(t) {
      if (t - st.last > 33) {
        st.rot += SPIN_STEP;
        // opts.frame(t) may return per-frame overrides (e.g. an animated phase + tint).
        var extra = opts.frame ? opts.frame(t) : null;
        render(canvas, Object.assign({}, opts, extra || {}, { rot: st.rot }));
        st.last = t;
      }
      st.raf = requestAnimationFrame(frame);
    }
    st.raf = requestAnimationFrame(frame);
    canvas.__spin = st;
  }
  function stop(canvas) {
    if (canvas && canvas.__spin) { cancelAnimationFrame(canvas.__spin.raf); canvas.__spin = null; }
  }

  // Per-planet gallery phase in 10-140 deg (radians): a per-page-load random seed mixed
  // with the planet id. Every refresh deals new phases across the grid; within one load a
  // planet's phase is stable, so filters / scrolling / hover never make cards flicker.
  var PHASE_SEED = (Math.random() * 0xffffffff) >>> 0;
  function hashPhase(id) {
    var h = 2166136261 ^ PHASE_SEED;
    for (var i = 0; i < id.length; i++) { h ^= id.charCodeAt(i); h = (h * 16777619) >>> 0; }
    var t = (h % 1000) / 999;
    return ((10 + 130 * t) * Math.PI) / 180;
  }

  // The 5-stop designer ramp, derived from the base hex. This is a straight port of
  // pipeline/palette/derive.py: same fixed lightness stops, same HLS round-trip, same
  // half-to-even rounding on the way back to 8-bit. It has to agree with Python exactly,
  // because the same ramp is rendered server-side on planet and tour pages — tests/
  // test_palette_ramp_js.py checks all ~11.5k palettes byte for byte.
  //
  // It lives here rather than in the index because it is a pure function of a hex the index
  // already carries: shipping five more hexes per planet (twice over, for the Roman view) was
  // ~29% of the gallery index for information every client can recompute in microseconds.
  // Built with the same expression as Python, NOT written out as literals: 0.88 - 0.18 is not
  // exactly 0.7 in binary, so the computed stops are 0.7049999999999998 / 0.8799999999999999.
  // Typing the round numbers instead lands the odd channel on the far side of a .5 boundary
  // and the ramps disagree with the server by 1/255.
  var RAMP_L_MIN = 0.18, RAMP_L_MAX = 0.88, RAMP_N = 5;
  var RAMP_L = [];
  for (var _i = 0; _i < RAMP_N; _i++) {
    RAMP_L.push(RAMP_L_MIN + ((RAMP_L_MAX - RAMP_L_MIN) * _i) / (RAMP_N - 1));
  }

  function pyRound(x) {
    // Python's round(): halves go to even, not up. Matters on exact .5 boundaries only.
    var f = Math.floor(x), d = x - f;
    if (d > 0.5) return f + 1;
    if (d < 0.5) return f;
    return f % 2 === 0 ? f : f + 1;
  }

  function rgbToHls(r, g, b) {
    var maxc = Math.max(r, g, b), minc = Math.min(r, g, b);
    var sumc = maxc + minc, rangec = maxc - minc, l = sumc / 2;
    if (minc === maxc) return [0, l, 0];
    var s = l <= 0.5 ? rangec / sumc : rangec / (2 - maxc - minc);
    var rc = (maxc - r) / rangec, gc = (maxc - g) / rangec, bc = (maxc - b) / rangec;
    var h = r === maxc ? bc - gc : g === maxc ? 2 + rc - bc : 4 + gc - rc;
    h = (h / 6) % 1;
    if (h < 0) h += 1;                       // JS % keeps sign; Python's does not
    return [h, l, s];
  }

  function hlsChannel(m1, m2, hue) {
    hue = hue % 1;
    if (hue < 0) hue += 1;
    if (hue < 1 / 6) return m1 + (m2 - m1) * hue * 6;
    if (hue < 0.5) return m2;
    if (hue < 2 / 3) return m1 + (m2 - m1) * (2 / 3 - hue) * 6;
    return m1;
  }

  function hlsToRgb(h, l, s) {
    if (s === 0) return [l, l, l];
    var m2 = l <= 0.5 ? l * (1 + s) : l + s - l * s;
    var m1 = 2 * l - m2;
    return [hlsChannel(m1, m2, h + 1 / 3), hlsChannel(m1, m2, h), hlsChannel(m1, m2, h - 1 / 3)];
  }

  function hex2 (n) { return (n < 16 ? "0" : "") + n.toString(16); }

  // base hex -> ["#rrggbb" x5], shade-2 → tint-2.
  function ramp(baseHex) {
    var h = String(baseHex || "").replace("#", "");
    if (h.length !== 6) return [baseHex, baseHex, baseHex, baseHex, baseHex];
    var r = parseInt(h.slice(0, 2), 16) / 255,
        g = parseInt(h.slice(2, 4), 16) / 255,
        b = parseInt(h.slice(4, 6), 16) / 255;
    var hls = rgbToHls(r, g, b);
    var out = [];
    for (var i = 0; i < RAMP_L.length; i++) {
      var c = hlsToRgb(hls[0], RAMP_L[i], hls[2]);
      out.push("#" + hex2(pyRound(c[0] * 255)) + hex2(pyRound(c[1] * 255)) + hex2(pyRound(c[2] * 255)));
    }
    return out;
  }

  // ---- The wax/wane phase cycle ----------------------------------------------------------
  // The hero on a planet page and the active stop on a tour page run the SAME cycle, and used
  // to run it from two copies of this arithmetic. They drifted: the tour let the colour index
  // reach the LAST phase entry — 180°, the fully backlit disc — and painted the planet black,
  // while the planet page had always stopped one entry short. One implementation now, so the
  // cycle can only be right or wrong everywhere at once.
  //
  // The light orbits 0-360°: full -> waning (shadow closes in from the left) -> a brief dark
  // moment -> waxing (light returns on the left) -> full again. That full sweep is the
  // GEOMETRY. The COLOUR index tracks the side-agnostic illumination at the nearest 10° stop
  // and stops one short of the end: the last entry is the unlit disc, which has no colour to
  // show and reads as a bug rather than a phase.
  var PHASE_SPEED = 16;  // degrees per second

  // Nearest 10° stop into a phase-colour list, never the final (unlit) entry.
  function phaseIndex(effDeg, nPhases) {
    return Math.max(0, Math.min((nPhases || 1) - 2, Math.round(effDeg / 10)));
  }

  // A stateful stepper: hand it the frame timestamp, get back where the cycle now stands.
  // `deg` is the geometry (0-360), `eff` the illumination the readout should name (0-170),
  // `idx` the phase-colour entry to tint with.
  function phaseCycle(startDeg, nPhases) {
    var deg = startDeg || 0, last = null;
    return function (t) {
      if (last === null) last = t;
      deg += PHASE_SPEED * (Math.min(t - last, 100) / 1000);
      last = t;
      if (deg >= 360) deg -= 360;
      var raw = deg <= 180 ? deg : 360 - deg;
      var idx = phaseIndex(raw, nPhases);
      return { deg: deg, rad: (deg * Math.PI) / 180, eff: Math.min(raw, idx * 10), idx: idx };
    };
  }

  window.PlanetRender = {
    render: render, spin: spin, stop: stop, hashPhase: hashPhase, ramp: ramp,
    phaseCycle: phaseCycle, phaseIndex: phaseIndex, PHASE_SPEED: PHASE_SPEED,
    preload: preload, onTexture: onTexture, ringAspect: ringAspect,
  };
})();
