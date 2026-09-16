(function () {
    "use strict";

    const mapContainer = document.getElementById("map-container");
    if (!mapContainer) {
        return;
    }

    const COLOR_SCALE = ["#eef2ff", "#c7d2fe", "#818cf8", "#4f46e5", "#312e81"];

    function colorForCount(count, maxCount) {
        if (count === 0 || maxCount === 0) {
            return "#f3f4f6";
        }
        const ratio = count / maxCount;
        const index = Math.min(COLOR_SCALE.length - 1, Math.floor(ratio * COLOR_SCALE.length));
        return COLOR_SCALE[index];
    }

    function findDepartmentPath(svg, code) {
        return (
            svg.querySelector('[id="' + code + '"]') ||
            svg.querySelector('[id="FR-' + code + '"]') ||
            svg.querySelector('[data-code="' + code + '"]')
        );
    }

    function applyColors(svg, ranking) {
        const counts = {};
        ranking.forEach(function (row) {
            counts[row.origin__code] = row.nombre;
        });
        const maxCount = Math.max(0, ...Object.values(counts));

        const unmatched = [];
        Object.keys(counts).forEach(function (code) {
            const path = findDepartmentPath(svg, code);
            if (!path) {
                unmatched.push(code);
                return;
            }
            path.setAttribute("fill", colorForCount(counts[code], maxCount));
        });

        if (unmatched.length > 0) {
            console.warn(
                "Carte : aucun trace trouve pour les codes suivants, verifier le fichier SVG et findDepartmentPath() :",
                unmatched
            );
        }
    }

    let svgRoot = null;

    fetch(mapContainer.dataset.svgUrl)
        .then(function (response) {
            return response.text();
        })
        .then(function (svgText) {
            mapContainer.innerHTML = svgText;
            svgRoot = mapContainer.querySelector("svg");
            const initialRanking = JSON.parse(document.getElementById("ranking-data").textContent);
            applyColors(svgRoot, initialRanking);
        });

    window.updateMapColors = function (ranking) {
        if (svgRoot) {
            applyColors(svgRoot, ranking);
        }
    };
})();
