/* Scope sweep for the "How we get the colours" diagrams.
 *
 * The explainer's diagrams are inline SVG line art in the oscilloscope costume, so the honest
 * animation for them is the one a real scope does: the trace paints itself left to right, and
 * the labels arrive after the line they annotate. Each diagram plays once, the first time it
 * scrolls into view, so a reader meets it drawing rather than already drawn.
 *
 * Everything visual lives in style.css. This file only supplies the three things CSS cannot
 * work out for itself:
 *   - the length of each path, so a stroke can be drawn on rather than faded in,
 *   - the running order (document order, which is already the logical left-to-right order),
 *   - the "in view" trigger, and a REPLAY control per diagram.
 *
 * Progressive enhancement throughout: with this file blocked the diagrams are simply static,
 * which is what they were before. With prefers-reduced-motion set, nothing animates and no
 * replay control is offered — the reader has asked for stillness, not for a play button.
 *
 * Kept out of app.js deliberately (see CLAUDE.md): that file is where parallel sessions collide.
 */
(function () {
  "use strict";

  var STEP_MS = 70; // stagger between one element and the next, in document order

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var page = document.querySelector(".how");
    if (!page) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    var diagrams = Array.prototype.slice.call(page.querySelectorAll(".dg"));
    if (!diagrams.length) return;

    /* Measure once, up front: a drawn-on stroke needs its own length as the dash pattern, and
     * asking for it later would interleave layout reads with the class writes below. */
    diagrams.forEach(function (svg) {
      var order = 0;
      Array.prototype.forEach.call(svg.children, function walk(node) {
        if (node.tagName === "defs") return;
        if (node.children && node.children.length && node.tagName === "g") {
          Array.prototype.forEach.call(node.children, walk);
          return;
        }
        node.style.setProperty("--i", order++);
        /* Only a solid, actually-stroked shape can draw itself. A dashed one already owns its
         * dash pattern (overwriting it would erase the dashes), and a fill-only shape — the
         * rainbow strips, the hatched blind zone — has no stroke to draw, so a dash animation
         * would leave it visible from the first frame instead of waiting its turn. Both fade. */
        if (typeof node.getTotalLength !== "function") return;
        if (node.classList.contains("dash") || node.classList.contains("dot")) return;
        var stroke = window.getComputedStyle(node).stroke;
        if (!stroke || stroke === "none") return;
        var len = 0;
        try {
          len = node.getTotalLength();
        } catch (e) {
          return; // a shape this browser will not measure: it falls back to fading in
        }
        if (len > 0) {
          node.style.setProperty("--len", Math.ceil(len));
          node.classList.add("dg-draw");
        }
      });
      svg.classList.add("dg-anim");
    });

    // Set the moment the observer delivers anything at all, intersecting or not: proof that the
    // trigger works, and the flag the rescue below stands down for.
    var triggerAlive = false;

    function play(svg) {
      svg.classList.remove("dg-live");
      // Reflow between the two writes, or the class never leaves and nothing restarts.
      void svg.getBoundingClientRect();
      svg.classList.add("dg-live");
    }

    /* Safety net, and the reason the pre-play hide is worth risking at all: a diagram waiting its
     * turn sits at opacity 0, so anything that stops the trigger firing would leave blank frames
     * where the science should be. If the observer has said nothing by the deadline, stop waiting
     * and draw all five — the sweep degrades to "already drawn", never to "missing".
     *
     * A backgrounded tab is the ordinary case: it paints no frames, so no callback arrives and no
     * reader is being short-changed. Hence the visibility check, and the re-arm on the way back. */
    function rescue() {
      if (triggerAlive) return;
      if (document.visibilityState === "hidden") return;
      diagrams.forEach(play);
    }
    setTimeout(rescue, 4000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible") setTimeout(rescue, 1500);
    });

    /* One REPLAY per diagram, injected rather than written into the template: the control only
     * means anything when this file is running. */
    diagrams.forEach(function (svg) {
      var bar = document.createElement("div");
      bar.className = "dg-bar";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dg-replay";
      btn.textContent = "▷ REPLAY";
      btn.setAttribute("aria-label", "Replay this diagram's animation");
      btn.addEventListener("click", function () {
        play(svg);
      });
      bar.appendChild(btn);
      svg.parentNode.insertBefore(bar, svg.nextSibling);
    });

    if (!("IntersectionObserver" in window)) {
      diagrams.forEach(play);
      return;
    }

    var seen = new IntersectionObserver(
      function (entries) {
        triggerAlive = true;
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          play(entry.target);
          seen.unobserve(entry.target); // first view only; REPLAY handles the rest
        });
      },
      // Enough of the diagram on screen that the sweep is not half-missed above the fold.
      { threshold: 0.35 }
    );
    diagrams.forEach(function (svg) {
      seen.observe(svg);
    });

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
