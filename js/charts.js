/* ============================================================
   FIT2179 DV2 — Chart loader
   Loads each Vega-Lite JSON spec into its slot on the page.
   ============================================================ */

const CHARTS = [
  { slot: "chart-01", file: "charts/01-median-age-hook.json" },
  { slot: "chart-02", file: "charts/02-population-pyramid.json" },
  { slot: "chart-03", file: "charts/03-births-vs-deaths.json" },
  { slot: "chart-04", file: "charts/04-tfr-slope.json" },
  { slot: "chart-05", file: "charts/05-world-speed-of-ageing.json" },
  { slot: "chart-06", file: "charts/06-life-expectancy-bump.json" },
  { slot: "chart-07", file: "charts/07-state-65plus-map.json" },
  { slot: "chart-08", file: "charts/08-state-slope.json" },
  { slot: "chart-09", file: "charts/09-age-bands-stacked.json" },
  { slot: "chart-10", file: "charts/10-state-bubbles-overlay.json" }
];

const VEGA_OPTIONS = {
  renderer: "svg",
  actions: false,  // hide the burger menu (no export/edit/etc)
  config: {
    background: null,
    autosize: { type: "fit", contains: "padding" }
  }
};

function loadChart({ slot, file }) {
  const el = document.getElementById(slot);
  if (!el) return;
  return vegaEmbed("#" + slot, file, VEGA_OPTIONS)
    .then(() => {
      // Clear the "Loading…" placeholder if it's still there
      const loader = el.querySelector(".chart-loading");
      if (loader) loader.remove();
    })
    .catch((err) => {
      el.innerHTML =
        '<div class="chart-error">Could not load <code>' +
        file +
        "</code><br><br>" +
        (err.message || err) +
        "</div>";
    });
}

// Load all charts. Could be lazy-loaded with IntersectionObserver later;
// for now we load them all on page load (total chart payload is ~2 MB).
document.addEventListener("DOMContentLoaded", () => {
  CHARTS.forEach(loadChart);
});
