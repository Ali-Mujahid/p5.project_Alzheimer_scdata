"use strict";
document.addEventListener("DOMContentLoaded", async () => {
  const select = document.getElementById("teTrendFamily");
  if (!select) return;
  const status = document.getElementById("teTrendStatus");
  const groups = ["WT_3mo", "WT_6mo", "WT_21mo", "5xFAD_3mo", "APOE4_3mo"];
  try {
    const response = await fetch("downloads/Microglia_group_peak_TE_copy_trends.tsv");
    if (!response.ok) throw new Error(`Data request ${response.status}`);
    const lines = (await response.text()).trim().split(/\r?\n/);
    const header = lines.shift().split("\t");
    const rows = lines.map(line => Object.fromEntries(line.split("\t").map((value, i) => [header[i], value])));
    const lookup = new Map(rows.map(row => [`${row.condition}\t${row.feature}`, row]));
    const baseFeatures = rows.filter(row => row.condition === "WT_3mo" && row.feature !== "ALL_CANONICAL_TE");
    if (baseFeatures.length !== 233 || baseFeatures.some(row => Number(row.reference_copies) <= 2000)) {
      throw new Error("Unexpected subfamily copy threshold or feature count");
    }
    baseFeatures.sort((a, b) => Number(b.reference_copies) - Number(a.reference_copies));
    for (const row of baseFeatures) {
      const option = document.createElement("option");
      option.value = row.feature;
      option.textContent = `${row.feature.replace("|", " / ")} · ${Number(row.reference_copies).toLocaleString()} copies`;
      select.append(option);
    }
    const total = groups.map(group => 100 * Number(lookup.get(`${group}\tALL_CANONICAL_TE`).peak_TE_overlap_fraction));
    new Chart(document.getElementById("teTrendTotalChart"), {
      type: "bar",
      data: { labels: groups, datasets: [{ label: "TE-overlapping peak summits (%)", data: total, backgroundColor: ["#3475ae", "#6ca2c7", "#92b8cf", "#c66a6a", "#9b6aae"] }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Peak summits within annotated TE (%)" } } } }
    });
    const familyChart = new Chart(document.getElementById("teTrendFamilyChart"), {
      type: "line",
      data: { labels: groups, datasets: [{ label: "Observed / expected TE-copy overlap", data: [], borderColor: "#8a4a9f", backgroundColor: "#8a4a9f", pointRadius: 5, borderWidth: 2, tension: 0.15 }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Observed / expected" } } } }
    });
    const update = () => {
      const feature = select.value;
      const values = groups.map(group => Number(lookup.get(`${group}\t${feature}`).observed_expected_ratio));
      familyChart.data.datasets[0].data = values;
      familyChart.update();
      const control = values[0];
      document.getElementById("teTrendContrasts").innerHTML = groups.slice(1).map((group, i) =>
        `<tr><td>WT_3mo vs ${group}</td><td>${values[i + 1].toFixed(3)}</td><td>${(values[i + 1] - control).toFixed(3)}</td></tr>`
      ).join("");
    };
    select.addEventListener("change", update);
    update();
    status.textContent = "233 eligible subfamilies; strictly more than 2,000 mm10 copies.";
  } catch (error) {
    status.textContent = `Trend data unavailable: ${error.message}`;
  }
});
