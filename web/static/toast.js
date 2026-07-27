// Transient confirmation readout ("copied #c3ccdf") for clipboard actions.
//
// This used to be a `<span>` inside the button rows, shown with x-show — so every copy
// grew the row and shoved COMPARE / .ASE sideways, then snapped them back 1.6 s later.
// A fixed overlay says the same thing without touching the layout.
//
// Deliberately dependency-free and global (`window.exoToast`) rather than Alpine state:
// the copy buttons live in several different components (planet detail, the lamp panel,
// the tour strip), and one shared element beats one flash variable per component.
(function () {
  "use strict";

  var el = null, timer = 0;
  var HOLD_MS = 1900;

  function node() {
    if (el) return el;
    el = document.createElement("div");
    el.className = "toast";
    // "status" + polite: a copy confirmation is worth announcing, never worth interrupting.
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.innerHTML = '<i class="toast-led" aria-hidden="true"></i><span class="toast-msg"></span>';
    document.body.appendChild(el);
    return el;
  }

  window.exoToast = function (msg) {
    if (!msg) return;
    var n = node();
    n.querySelector(".toast-msg").textContent = msg;
    // Copying twice in a row should re-play the entry, not sit there looking inert.
    n.classList.remove("on");
    void n.offsetWidth;  // force reflow so the transition restarts
    n.classList.add("on");
    clearTimeout(timer);
    timer = setTimeout(function () { n.classList.remove("on"); }, HOLD_MS);
  };
})();
