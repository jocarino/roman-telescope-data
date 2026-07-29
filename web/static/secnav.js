/* Sticky section tabs on the planet page.
 *
 * Progressive enhancement, deliberately: the markup is plain <a href="#sec-..."> anchors, so
 * the jump works with JavaScript off, with the sticky bar handled entirely in CSS. This file
 * only adds the two things CSS cannot do — the "you are here" highlight, and easing the jump
 * instead of teleporting.
 *
 * Kept out of app.js for the same reason as modelspace.js: that file is where parallel
 * sessions on this repo collide (see CLAUDE.md).
 */
(function () {
  "use strict";

  document.addEventListener("alpine:init", function () {
    Alpine.data("secnav", function () {
      return {
        active: "",
        stuck: false,
        _ids: [],

        init() {
          this._ids = Array.prototype.map.call(
            this.$el.querySelectorAll("[data-sec]"),
            function (a) { return a.dataset.sec; }
          );
          this.active = this._ids[0] || "";
          // The page can load already scrolled — a back-navigation, or a #sec-... deep link.
          this.$nextTick(() => this.onScroll());
        },

        /* The current section is the LAST one whose top has passed under the bar. Reading
         * positions on scroll rather than using IntersectionObserver is deliberate: these
         * panels are far taller than the viewport, so a "which one is visible" test has
         * several answers at once and flickers between them. "Which one have I reached"
         * has exactly one. */
        onScroll() {
          var bar = this.$el.getBoundingClientRect();
          this.stuck = bar.top <= 0.5;
          var edge = bar.height + 12;
          var current = this._ids[0];
          for (var i = 0; i < this._ids.length; i++) {
            var el = document.getElementById(this._ids[i]);
            if (el && el.getBoundingClientRect().top <= edge) current = this._ids[i];
          }
          // The last section is shorter than the viewport, so once the page bottoms out its
          // top still sits well below the bar and "which one have I reached" never picks it —
          // its tab would be the one tab that never lights up. Hitting the bottom of the page
          // IS reaching the last section.
          var doc = document.documentElement;
          if (window.innerHeight + window.scrollY >= doc.scrollHeight - 2) {
            current = this._ids[this._ids.length - 1];
          }
          if (current !== this.active) this.active = current;
        },

        go(event, id) {
          var el = document.getElementById(id);
          if (!el) return;  // never swallow the click: let the plain anchor try
          event.preventDefault();
          el.scrollIntoView({ behavior: "smooth", block: "start" });
          // replaceState, not a hash assignment: setting location.hash would re-jump and
          // undo the smooth scroll, and would also push a history entry per tab press.
          if (window.history && history.replaceState) {
            history.replaceState(null, "", "#" + id);
          }
          this.active = id;
        },
      };
    });
  });
})();
