(function () {
    "use strict";

    const toggleButton = document.getElementById("themeToggle");
    if (!toggleButton) {
        return;
    }

    function currentTheme() {
        return document.documentElement.getAttribute("data-theme") || "dark";
    }

    function updateIcon() {
        toggleButton.textContent = currentTheme() === "dark" ? "☀️" : "🌙";
    }

    updateIcon();

    toggleButton.addEventListener("click", function () {
        const next = currentTheme() === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        updateIcon();
        try {
            localStorage.setItem("theme", next);
        } catch (e) {
            // localStorage indisponible : le choix ne sera pas retenu au prochain chargement.
        }
        document.dispatchEvent(new CustomEvent("themechange", { detail: { theme: next } }));
    });
})();
