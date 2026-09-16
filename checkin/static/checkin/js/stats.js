(function () {
    "use strict";

    const keyFiguresEl = document.getElementById("key-figures");
    if (!keyFiguresEl) {
        return;
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
            datasets: [{ label: "Visiteurs", data: rankingData.map(function (row) { return row.nombre; }) }],
        },
        options: { indexAxis: "y", responsive: true },
    });

    const evolutionChart = new Chart(document.getElementById("evolution-chart"), {
        type: "line",
        data: {
            labels: evolutionData.map(function (row) { return row.heure; }),
            datasets: [{ label: "Enregistrements par heure", data: evolutionData.map(function (row) { return row.nombre; }) }],
        },
        options: { responsive: true },
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
