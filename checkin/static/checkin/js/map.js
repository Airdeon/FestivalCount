(function () {
    "use strict";

    const mapContainer = document.getElementById("map-container");
    if (!mapContainer) {
        return;
    }

    function cssVar(name, fallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    }

    function hexToRgb(hex) {
        const clean = hex.replace("#", "").trim();
        const bigint = parseInt(clean, 16);
        return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
    }

    function interpolateColor(hexStart, hexEnd, ratio) {
        const start = hexToRgb(hexStart);
        const end = hexToRgb(hexEnd);
        const mixed = start.map(function (channel, index) {
            return Math.round(channel + (end[index] - channel) * ratio);
        });
        return "rgb(" + mixed.join(",") + ")";
    }

    function colorForCount(count, maxCount) {
        if (count === 0 || maxCount === 0) {
            return cssVar("--color-map-empty", "#e2e8f0");
        }
        const ratio = count / maxCount;
        const low = cssVar("--color-map-low", "#93c5fd");
        const high = cssVar("--color-map-high", "#1d4ed8");
        return interpolateColor(low, high, ratio);
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

        svg.querySelectorAll("path").forEach(function (path) {
            path.setAttribute("fill", cssVar("--color-map-empty", "#e2e8f0"));
            path.setAttribute("stroke", cssVar("--color-surface-border", "#9ca3af"));
            path.setAttribute("stroke-width", "0.5");
        });

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
    let lastRanking = [];

    fetch(mapContainer.dataset.svgUrl)
        .then(function (response) {
            return response.text();
        })
        .then(function (svgText) {
            mapContainer.innerHTML = svgText;
            svgRoot = mapContainer.querySelector("svg");
            lastRanking = JSON.parse(document.getElementById("ranking-data").textContent);
            applyColors(svgRoot, lastRanking);
        });

    window.updateMapColors = function (ranking) {
        lastRanking = ranking;
        if (svgRoot) {
            applyColors(svgRoot, ranking);
        }
    };

    document.addEventListener("themechange", function () {
        if (svgRoot) {
            applyColors(svgRoot, lastRanking);
        }
    });
})();
