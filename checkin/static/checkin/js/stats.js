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

    const rankingData = JSON.parse(document.getElementById("ranking-data").textContent);
    const evolutionData = JSON.parse(document.getElementById("evolution-data").textContent);

    const rankingChart = new Chart(document.getElementById("ranking-chart"), {
        type: "bar",
        data: {
            labels: rankingData.map(function (row) { return row.origin__code; }),
            datasets: [{
                label: "Visiteurs",
                data: rankingData.map(function (row) { return row.nombre; }),
                backgroundColor: chartColors().accent,
            }],
        },
        options: chartOptionsWithTheme({ indexAxis: "y" }),
    });

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

        rankingChart.data.labels = data.ranking.map(function (row) { return row.origin__code; });
        rankingChart.data.datasets[0].data = data.ranking.map(function (row) { return row.nombre; });
        rankingChart.update();

        evolutionChart.data.labels = data.hourly_evolution.map(function (row) { return row.heure; });
        evolutionChart.data.datasets[0].data = data.hourly_evolution.map(function (row) { return row.nombre; });
        evolutionChart.update();

        if (window.updateMapColors) {
            window.updateMapColors(data.ranking);
        }
    }

    function refreshChartTheme() {
        const colors = chartColors();
        [rankingChart, evolutionChart].forEach(function (chart) {
            chart.options.color = colors.text;
            chart.options.scales.x.ticks.color = colors.text;
            chart.options.scales.x.grid.color = colors.grid;
            chart.options.scales.y.ticks.color = colors.text;
            chart.options.scales.y.grid.color = colors.grid;
            chart.options.plugins.legend.labels.color = colors.text;
            chart.data.datasets[0].backgroundColor = colors.accent;
            if (chart.data.datasets[0].borderColor) {
                chart.data.datasets[0].borderColor = colors.accent;
            }
            chart.update();
        });
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
