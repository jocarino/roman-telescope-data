// Visitor analytics (PostHog). Loaded ONLY when the build carried a project key.
//
// base.html emits this file — and PostHog's library — behind `{% if site.posthog_key %}`,
// which is set from --posthog-key / $POSTHOG_KEY at build time. That gate is the whole
// design: without it, every `exohub serve` worktree, every local dist/ and the 390px mobile
// iframe harness would file their browsing into the same dashboard as real visitors and
// quietly wreck the numbers. Preview builds send nothing because they contain nothing.
//
// The install is deliberately narrow:
//   * Cookieless (`cookieless_mode: "always"`). The site has no accounts and nothing to
//     personalise, so there is no cookie worth asking consent for and no banner on a page
//     whose entire job is to show you a colour. The honest cost: PostHog rotates the
//     identifying salt daily, so one person visiting on two days counts as two people —
//     visitor totals read high and retention means nothing here. Pageviews and event
//     counts, which is what we actually ask about, are unaffected.
//     NOTE: this requires "Cookieless server hash mode" to be ON in the PostHog project
//     (Project settings -> Web analytics). Without it, events are dropped.
//   * No autocapture, no session replay, no heatmaps. A DOM firehose answers none of the
//     questions this site has ("does anyone flip the Roman switch?") and costs far more
//     events than the handful below.
//   * A fixed vocabulary, named so it still reads a year from now.
//
// Everything here is wrapped so an analytics failure can never take the page with it, and
// call sites elsewhere use `window.exoTrack && window.exoTrack(...)` — the same guard as
// window.exoToast — so the site behaves identically when this file is absent.
(function () {
  "use strict";

  var cfg = window.EXO_ANALYTICS;
  var ph = window.posthog;

  // Campaign tags come off the URL once the pageview has carried them, so a URL copied out of
  // the address bar and re-posted doesn't credit its new audience to the old channel. When
  // there is no pageview coming there is nothing to wait for, so strip immediately.
  function stripCampaign() {
    if (window.ExoCampaign) window.ExoCampaign.strip();
  }

  // No key, or the library was blocked (ad blockers take it out routinely, which is fine and
  // must stay silent). Leaving window.exoTrack undefined makes every call site a no-op.
  if (!cfg || !cfg.key || !ph || typeof ph.init !== "function") { stripCampaign(); return; }

  try {
    ph.init(cfg.key, {
      api_host: cfg.api_host,
      cookieless_mode: "always",
      autocapture: false,
      capture_pageview: true,   // plain page loads: this is a multi-page static site, no router
      disable_session_recording: true,
      disable_surveys: true,
      // Nobody is ever identified here, so no person profiles are created either.
      person_profiles: "identified_only",
    });
  } catch (e) {
    stripCampaign();
    return;
  }

  // Wait for the pageview EVENT, not for init() to return: PostHog captures it from a
  // `setTimeout(…, 1)` inside its own loader, so anything synchronous here still runs first
  // and would delete ?utm_source= a millisecond before the pageview read it. `eventCaptured`
  // fires as the event is built, with the campaign properties already on it. If an older
  // library has no `on`, the tag simply stays in the URL — attribution is intact either way,
  // and that is the half that can't be recovered afterwards.
  if (typeof ph.on === "function") {
    var off = ph.on("eventCaptured", function (e) {
      if (!e || e.event !== "$pageview") return;
      if (off) off();
      stripCampaign();
    });
  }

  var timers = {};

  function send(name, props) {
    try {
      ph.capture(name, props || {});
    } catch (e) {
      /* analytics must never break the page */
    }
  }

  // `opts.debounce` (ms) collapses a burst into one event — the phase slider fires on every
  // step of a drag, and forty events per drag is noise that also eats the free tier.
  window.exoTrack = function (name, props, opts) {
    if (opts && opts.debounce) {
      clearTimeout(timers[name]);
      timers[name] = setTimeout(function () { send(name, props); }, opts.debounce);
      return;
    }
    send(name, props);
  };

  // Which worlds people actually open. The pageview already carries the path, but a named
  // event with the id on it turns "top planets this week" into one query instead of a regex
  // over ~5,800 URLs. Clean URLs mean the .html is optional — match either.
  var m = location.pathname.match(/^\/planet\/([^/]+?)(?:\.html)?$/);
  if (m) {
    send("planet_viewed", {
      planet_id: m[1],
      // Titles are "<name> · Exoplanet Palette"; the readable half is what a dashboard wants.
      planet_name: (document.title.split(" · ")[0] || "").trim(),
    });
  }

  // Palette downloads are plain <a download> links to /palettes/*.ase, so one delegated
  // listener covers every page that offers one without touching any of them.
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || typeof t.closest !== "function") return;
    var a = t.closest('a[href^="/palettes/"]');
    if (a) send("palette_downloaded", { file: (a.getAttribute("href") || "").split("/").pop() });
  });
})();
