/* ============================================================
   FIT2179 DV2 — Chart loader + lightbox
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

// Keep a cache of loaded specs so we can re-render them in the lightbox
const SPEC_CACHE = {};

const VEGA_OPTIONS = {
  renderer: "svg",
  actions: false,
  config: { background: null }
};

function loadChart({ slot, file }) {
  const el = document.getElementById(slot);
  if (!el) return;

  return fetch(file)
    .then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then((spec) => {
      SPEC_CACHE[slot] = spec; // remember for lightbox re-render
      return vegaEmbed("#" + slot, spec, VEGA_OPTIONS);
    })
    .then(() => {
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

// ============================================================
// Lightbox
// ============================================================

function openLightbox(slotId) {
  const spec = SPEC_CACHE[slotId];
  if (!spec) return; // chart not loaded yet

  // Build a copy of the spec sized larger for the lightbox
  const bigSpec = JSON.parse(JSON.stringify(spec));

  // Bump dimensions if they exist at the top level
  if (typeof bigSpec.width === "number") {
    bigSpec.width = Math.min(window.innerWidth - 80, Math.max(bigSpec.width * 1.4, 900));
  }
  if (typeof bigSpec.height === "number") {
    bigSpec.height = Math.min(window.innerHeight - 200, Math.max(bigSpec.height * 1.4, 500));
  }

  // For hconcat / vconcat / layered charts, also scale inner widths/heights
  ["hconcat", "vconcat", "concat"].forEach((key) => {
    if (Array.isArray(bigSpec[key])) {
      bigSpec[key].forEach((sub) => {
        if (typeof sub.width === "number") sub.width = Math.round(sub.width * 1.4);
        if (typeof sub.height === "number") sub.height = Math.round(sub.height * 1.4);
      });
    }
  });

  // Show the overlay
  const overlay = document.getElementById("lightbox");
  const target = document.getElementById("lightbox-chart");
  target.innerHTML = ""; // clear any previous chart
  overlay.classList.add("is-open");
  document.body.style.overflow = "hidden"; // prevent background scroll

  // Render the bigger chart inside the lightbox
  vegaEmbed("#lightbox-chart", bigSpec, VEGA_OPTIONS);
}

function closeLightbox() {
  const overlay = document.getElementById("lightbox");
  const target = document.getElementById("lightbox-chart");
  overlay.classList.remove("is-open");
  target.innerHTML = "";
  document.body.style.overflow = ""; // restore scroll
}

// ============================================================
// Wire up everything on DOMContentLoaded
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  // Inject lightbox markup once at the end of body
  const lightboxHtml =
    '<div id="lightbox" class="lightbox" aria-hidden="true" role="dialog">' +
      '<button class="lightbox__close" type="button" aria-label="Close">&times;</button>' +
      '<div id="lightbox-chart" class="lightbox__chart"></div>' +
    "</div>";
  document.body.insertAdjacentHTML("beforeend", lightboxHtml);

  // Attach close handlers
  const overlay = document.getElementById("lightbox");
  const closeBtn = overlay.querySelector(".lightbox__close");
  closeBtn.addEventListener("click", closeLightbox);
  overlay.addEventListener("click", (e) => {
    // close when clicking outside the chart
    if (e.target === overlay) closeLightbox();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });

  // Inject an expand button into each chart block
  CHARTS.forEach(({ slot }) => {
    const chartEl = document.getElementById(slot);
    if (!chartEl) return;
    const block = chartEl.parentElement; // the .chart-block wrapper
    if (!block) return;

    const btn = document.createElement("button");
    btn.className = "chart-expand";
    btn.type = "button";
    btn.setAttribute("aria-label", "View larger");
    btn.innerHTML = "⤢ Expand";
    btn.addEventListener("click", () => openLightbox(slot));
    // Insert at the start of the block so it sits above the chart
    block.appendChild(btn);
  });

  // Load all charts
  CHARTS.forEach(loadChart);
});
