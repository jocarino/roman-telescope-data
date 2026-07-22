// Procedural planet renderer. One shared offscreen WebGL context renders an analytic lit
// sphere (bands, haze, limb-darkening, terminator) from a planet's palette + attributes, then
// blits into any target canvas. Three styles: "smooth", "retro" (pixel), "modern" (pixel).
//
// Honest by construction: colour comes from the derived palette; texture (bands) is schematic.
// No external library, no build step.
(function () {
  "use strict";

  var VERT = "attribute vec2 p; varying vec2 v; void main(){ v = p; gl_Position = vec4(p,0.,1.); }";

  var FRAG = [
    "precision highp float;",
    "varying vec2 v;",
    "uniform vec3 pal[5];",
    "uniform float bandFreq, bandContrast, haze, brightness, light, dither, levels;",
    "uniform int pixel, outline;",
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
    "void main(){",
    "  vec2 uv = v;",
    "  float r2 = dot(uv,uv);",
    "  if(r2 > 1.0){ discard; }",
    "  float z = sqrt(1.0 - r2);",
    "  vec3 N = vec3(uv, z);",
    "  float lat = asin(clamp(uv.y,-1.,1.));",
    // Near-full phase: single soft day/night term + limb darkening.
    "  vec3 L = normalize(vec3(cos(light)*0.55, 0.28, 0.90));",
    "  float lit = smoothstep(-0.08, 0.42, dot(N, L));",
    "  float limb = pow(z, 0.30);",
    "  float shade = (0.34 + 0.66*lit) * limb;",
    "  float band = 0.5 + 0.5*sin(lat*bandFreq + sin(lat*bandFreq*0.5)*0.6);",
    "  band = mix(0.5, band, bandContrast);",
    "  float rim = smoothstep(0.74,1.0,r2);",
    "  float tone = shade * (0.60 + 0.44*band) * brightness + rim*haze*0.28;",
    // Pixel styles: dither THEN posterize -> clean flat colour bands with dithered edges.
    "  if(pixel==1){",
    "    tone = clamp(tone, 0.0, 1.0);",
    "    tone += bayer(gl_FragCoord.xy) * dither;",
    "    tone = floor(tone*levels + 0.5) / levels;",
    "  }",
    "  vec3 col = ramp(tone);",
    "  if(pixel==0){ col = mix(col, pal[4], rim*haze*0.4); }",  // smooth-only haze tint
    "  if(outline==1 && r2>0.90){ col *= 0.35; }",
    "  gl_FragColor = vec4(col, 1.0);",
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
    ["pal","bandFreq","bandContrast","haze","brightness","light","dither","levels","pixel","outline"]
      .forEach(function (n) { U[n] = gl.getUniformLocation(prog, n === "pal" ? "pal[0]" : n); });
    return true;
  }
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
    var base = hexToRgb(opts.palette[2] || opts.palette[0]);
    var haze = Math.max(0, base[2] - Math.max(base[0], base[1])) * 2.2; // blueness -> haze
    return { bandFreq: bandFreq, bandContrast: bandContrast, brightness: brightness, haze: Math.min(haze, 1) };
  }

  function render(target, opts) {
    if (!target || !opts || !opts.palette || !init()) return;
    var pixel = opts.style !== "smooth";
    var res = pixel ? 80 : 480;
    glCanvas.width = res; glCanvas.height = res;
    gl.viewport(0, 0, res, res);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    var d = derive(opts);
    var flat = [];
    for (var i = 0; i < 5; i++) {
      var c = hexToRgb(opts.palette[i] || opts.palette[opts.palette.length - 1]);
      flat.push(c[0], c[1], c[2]);
    }
    gl.uniform3fv(U.pal, new Float32Array(flat));
    gl.uniform1f(U.bandFreq, d.bandFreq);
    gl.uniform1f(U.bandContrast, d.bandContrast);
    gl.uniform1f(U.haze, d.haze);
    gl.uniform1f(U.brightness, d.brightness);
    gl.uniform1f(U.light, opts.light == null ? 0.0 : opts.light);
    gl.uniform1i(U.pixel, pixel ? 1 : 0);
    // retro = fewer, bolder colour bands + outline; modern = more bands, no outline. Dither
    // amplitude is ~one posterization step so transitions read as clean pixel-art gradients.
    var levels = opts.style === "retro" ? 5.0 : 8.0;
    gl.uniform1f(U.levels, levels);
    gl.uniform1f(U.dither, pixel ? 0.9 / levels : 0.0);
    gl.uniform1i(U.outline, opts.style === "retro" ? 1 : 0);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    // Blit 1:1 into the target canvas; CSS does the INTEGER upscale (80->160 = 2x) with
    // image-rendering:pixelated, so pixels stay uniform and crisp (this was the jank).
    target.width = res; target.height = res;
    var ctx = target.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(glCanvas, 0, 0);
  }

  window.PlanetRender = { render: render };
})();
