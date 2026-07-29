// Jargon tooltips. Every `<button class="gloss" data-term="…">` on the site shows its
// plain-English definition on hover, on tap, or on keyboard focus.
//
// One shared popover for the whole page, driven by delegated events on document — so terms
// that arrive later (the hold-to-peek card, JS-rendered gallery
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

  // Two sources, one popover. A glossary term looks its definition up in window.GLOSSARY; a
  // control (the jinfo [i] beside a readout or a knob) carries its own text in data-tip,
  // because a knob has no dictionary entry. data-tip-term is optional — without it the
  // popover drops its header bar and is just the explanation.
  function entry(node) {
    if (!node) return null;
    if (node.dataset.tip) return { t: node.dataset.tipTerm || "", s: node.dataset.tip };
    var g = window.GLOSSARY;
    return (g && g[node.dataset.term]) || null;
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
    pop.classList.toggle("no-term", !e.t);
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

  // Anything carrying data-term (a glossary word) or data-tip (a control's own explanation)
  // is explainable. The .gloss class only supplies the visual mark, so chips with their own
  // look (the measured/computed/assumed tags, the provenance badges) can opt into the
  // definition without fighting their own styling.
  function target(ev) {
    var t = ev.target;
    return t && t.closest ? t.closest("[data-term], [data-tip]") : null;
  }

  // Same mark, built in JS — for copy that isn't server-rendered (the compare table's row
  // labels, the census stat tiles). Text is escaped; ids come from our own code, never input.
  // An id with no entry degrades to plain text: a mark that explains nothing is worse than
  // no mark, and unlike the templates there is no build-time check to catch a typo here.
  window.glossHTML = function (id, text) {
    var d = document.createElement("div");
    d.textContent = text == null ? id : text;
    if (window.GLOSSARY && !window.GLOSSARY[id]) return d.innerHTML;
    return '<button type="button" class="gloss" data-term="' + id + '" aria-expanded="false">' +
      d.innerHTML + "</button>";
  };

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

  // Tap pins the definition open; tapping the same term again closes it. This is the only
  // path on touch, where there is no hover to rely on.
  document.addEventListener("click", function (ev) {
    var t = target(ev);
    if (!t) { if (cur) hide(); return; }
    ev.preventDefault();
    // Where the pointer hovers, hover already governs open AND close, and the popover is
    // mouse-enterable, so a click must not pin: pinning strands the box open after the
    // cursor leaves, and toggling it shut leaves the term dead under a cursor that hasn't
    // moved (no fresh mouseover fires until you leave and come back). On hover devices a
    // click just re-shows what hover was already showing.
    if (canHover) { show(t); return; }
    if (cur === t && pinned) { hide(); return; }
    show(t);
    pinned = true;
  });

  // Keyboard focus opens the definition too — but ONLY keyboard focus. A tap focuses the
  // button before the click lands, so treating every focusin as "open" meant the tap opened
  // it and the click that followed saw it already pinned and toggled it straight back shut:
  // two taps to see anything on touch. :focus-visible is exactly the "not a pointer" test.
  // Where it is unsupported we simply don't open on focus; Enter/Space still fire click, so
  // keyboard users keep a way in and touch users keep their single tap.
  function keyboardFocused(node) {
    try { return node.matches(":focus-visible"); } catch (e) { return false; }
  }

  document.addEventListener("focusin", function (ev) {
    var t = target(ev);
    if (t) { if (keyboardFocused(t)) { show(t); pinned = true; } }
    else if (cur && pinned) hide();
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && cur) hide();
  });

  // The popover is fixed-positioned, so it has to follow (or leave) when the page moves.
  window.addEventListener("scroll", function () { if (cur) place(cur); }, { passive: true });
  window.addEventListener("resize", hide);
})();
