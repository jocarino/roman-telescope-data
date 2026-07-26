// Jargon tooltips. Every `<button class="gloss" data-term="…">` on the site shows its
// plain-English definition on hover, on tap, or on keyboard focus.
//
// One shared popover for the whole page, driven by delegated events on document — so terms
// that arrive later (the htmx planet drawer, the hold-to-peek card, JS-rendered gallery
// cards) need no wiring at all. Definitions come from window.GLOSSARY, emitted at build time
// from data/glossary.json. If that file is missing the marks stay readable and simply do
// nothing, which is the honest failure mode for an explanation layer.
(function () {
  "use strict";

  var pop = null;      // the single popover element, created on first use
  var cur = null;      // the .gloss currently explained, or null
  var pinned = false;  // true when opened by click/tap: hover no longer closes it
  var canHover = false;
  try { canHover = window.matchMedia("(hover: hover)").matches; } catch (e) { /* ignore */ }

  function entry(node) {
    var g = window.GLOSSARY;
    return (g && node && g[node.dataset.term]) || null;
  }

  function build() {
    pop = document.createElement("div");
    pop.className = "gloss-pop";
    pop.id = "gloss-pop";
    pop.setAttribute("role", "tooltip");
    pop.innerHTML = '<b class="gloss-pop-term"></b><span class="gloss-pop-def"></span>';
    document.body.appendChild(pop);
    return pop;
  }

  // Above the term when there is room, below it otherwise; always clamped inside the
  // viewport so a term at the far right of a table never pushes the box off-screen.
  function place(node) {
    var r = node.getBoundingClientRect();
    var w = pop.offsetWidth, h = pop.offsetHeight, pad = 10;
    var left = Math.round(r.left + r.width / 2 - w / 2);
    left = Math.max(pad, Math.min(left, window.innerWidth - w - pad));
    var top = Math.round(r.top - h - 8);
    if (top < pad) top = Math.round(r.bottom + 8);
    pop.style.left = left + "px";
    pop.style.top = top + "px";
  }

  function show(node) {
    var e = entry(node);
    if (!e) return;
    if (!pop) build();
    pop.querySelector(".gloss-pop-term").textContent = e.t;
    pop.querySelector(".gloss-pop-def").textContent = e.s;
    if (cur && cur !== node) {
      cur.classList.remove("on");
      cur.removeAttribute("aria-describedby");
    }
    cur = node;
    node.classList.add("on");
    node.setAttribute("aria-expanded", "true");
    // Pointed at the popover only while it holds THIS term's definition.
    node.setAttribute("aria-describedby", "gloss-pop");
    pop.classList.add("open");
    place(node);
  }

  function hide() {
    pinned = false;
    if (cur) {
      cur.classList.remove("on");
      cur.setAttribute("aria-expanded", "false");
      cur.removeAttribute("aria-describedby");
    }
    cur = null;
    if (pop) pop.classList.remove("open");
  }

  function target(ev) {
    var t = ev.target;
    return t && t.closest ? t.closest(".gloss") : null;
  }

  if (canHover) {
    document.addEventListener("mouseover", function (ev) {
      var t = target(ev);
      if (t) show(t);
      else if (cur && !pinned && !(ev.target.closest && ev.target.closest(".gloss-pop"))) hide();
    });
    // Leaving the window entirely fires no mouseover, so close here or a hover tooltip
    // could be left hanging over the page.
    document.addEventListener("mouseleave", function () { if (!pinned) hide(); });
  }

  // Tap (and click) pins the definition open; tapping the same term again closes it. This is
  // the only path on touch, where there is no hover to rely on.
  document.addEventListener("click", function (ev) {
    var t = target(ev);
    if (!t) { if (cur) hide(); return; }
    ev.preventDefault();
    if (cur === t && pinned) { hide(); return; }
    show(t);
    pinned = true;
  });

  document.addEventListener("focusin", function (ev) {
    var t = target(ev);
    if (t) { show(t); pinned = true; } else if (cur && pinned) hide();
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && cur) hide();
  });

  // The popover is fixed-positioned, so it has to follow (or leave) when the page moves.
  window.addEventListener("scroll", function () { if (cur) place(cur); }, { passive: true });
  window.addEventListener("resize", hide);
})();
