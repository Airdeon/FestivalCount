(function () {
    "use strict";

    const keyFiguresEl = document.getElementById("key-figures");
    if (!keyFiguresEl) {
        return;
    }

    function cssVar(name, fallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    }

    function chartColors() {
        return {
            text: cssVar("--color-text", "#1a1a1a"),
            grid: cssVar("--color-surface-border", "#e5e7eb"),
            accent: cssVar("--color-accent-solid", "#2563eb"),
        };
    }

    function chartOptionsWithTheme(extra) {
        const colors = chartColors();
        return Object.assign(
            {
                responsive: true,
                color: colors.text,
                scales: {
                    x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                    y: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                },
                plugins: {
                    legend: { labels: { color: colors.text } },
                },
            },
            extra || {}
        );
    }

    const statsDataUrl = keyFiguresEl.dataset.statsDataUrl;
    const editionId = keyFiguresEl.dataset.editionId;
    const isCurrentEdition = keyFiguresEl.dataset.isCurrent === "true";

    const evolutionData = JSON.parse(document.getElementById("evolution-data").textContent);

    const evolutionChart = new Chart(document.getElementById("evolution-chart"), {
        type: "line",
        data: {
            labels: evolutionData.map(function (row) { return row.heure; }),
            datasets: [{
                label: "Enregistrements par heure",
                data: evolutionData.map(function (row) { return row.nombre; }),
                borderColor: chartColors().accent,
                backgroundColor: chartColors().accent,
            }],
        },
        options: chartOptionsWithTheme(),
    });

    function applyData(data) {
        document.getElementById("total-visiteurs").textContent = data.key_figures.total_visiteurs;
        document.getElementById("total-departements").textContent = data.key_figures.nombre_departements;
        document.getElementById("total-pays").textContent = data.key_figures.nombre_pays;

        evolutionChart.data.labels = data.hourly_evolution.map(function (row) { return row.heure; });
        evolutionChart.data.datasets[0].data = data.hourly_evolution.map(function (row) { return row.nombre; });
        evolutionChart.update();

        if (window.updateMapColors) {
            window.updateMapColors(data.ranking);
        }
    }

    function refreshChartTheme() {
        const colors = chartColors();
        evolutionChart.options.color = colors.text;
        evolutionChart.options.scales.x.ticks.color = colors.text;
        evolutionChart.options.scales.x.grid.color = colors.grid;
        evolutionChart.options.scales.y.ticks.color = colors.text;
        evolutionChart.options.scales.y.grid.color = colors.grid;
        evolutionChart.options.plugins.legend.labels.color = colors.text;
        evolutionChart.data.datasets[0].backgroundColor = colors.accent;
        if (evolutionChart.data.datasets[0].borderColor) {
            evolutionChart.data.datasets[0].borderColor = colors.accent;
        }
        evolutionChart.update();
    }

    document.addEventListener("themechange", refreshChartTheme);

    if (isCurrentEdition) {
        window.setInterval(function () {
            fetch(statsDataUrl + "?edition=" + editionId)
                .then(function (response) {
                    return response.json();
                })
                .then(applyData)
                .catch(function () {
                    // Échec silencieux : nouvelle tentative au prochain intervalle.
                });
        }, 30000);
    }
})();
