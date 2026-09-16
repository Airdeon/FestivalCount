(function () {
    "use strict";

    const screenGroups = document.getElementById("screen-groups");
    if (!screenGroups) {
        return;
    }

    const origins = JSON.parse(document.getElementById("origins-data").textContent);
    const createUrl = screenGroups.dataset.createUrl;
    const cancelUrlBase = screenGroups.dataset.cancelUrlBase;

    const groupButtonsEl = document.getElementById("group-buttons");
    const originButtonsEl = document.getElementById("origin-buttons");
    const screenOrigins = document.getElementById("screen-origins");
    const selectedGroupTitle = document.getElementById("selected-group-title");
    const backButton = document.getElementById("back-button");
    const confirmationEl = document.getElementById("confirmation");
    const confirmationText = document.getElementById("confirmation-text");
    const cancelButton = document.getElementById("cancel-button");
    const errorMessageEl = document.getElementById("error-message");
    const autreForm = document.getElementById("autre-form");
    const autreInput = document.getElementById("autre-input");
    const autreSubmit = document.getElementById("autre-submit");

    let confirmationTimeoutId = null;
    let lastVisitId = null;

    function getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    }

    function groupsInOrder() {
        const seen = [];
        origins.forEach(function (origin) {
            if (seen.indexOf(origin.groupe) === -1) {
                seen.push(origin.groupe);
            }
        });
        return seen;
    }

    function showScreenGroups() {
        screenOrigins.hidden = true;
        screenGroups.hidden = false;
        autreForm.hidden = true;
    }

    function showScreenOrigins(groupe) {
        selectedGroupTitle.textContent = groupe;
        originButtonsEl.innerHTML = "";
        autreForm.hidden = true;

        origins
            .filter(function (origin) {
                return origin.groupe === groupe;
            })
            .forEach(function (origin) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "origin-button";
                button.textContent = origin.type === "departement" ? origin.code + " " + origin.nom : origin.nom;
                button.addEventListener("click", function () {
                    if (origin.type === "autre") {
                        autreForm.hidden = false;
                        autreInput.value = "";
                        autreInput.focus();
                    } else {
                        submitVisit(origin.code, "");
                    }
                });
                originButtonsEl.appendChild(button);
            });

        screenGroups.hidden = true;
        screenOrigins.hidden = false;
    }

    function renderGroups() {
        groupsInOrder().forEach(function (groupe) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "group-button";
            button.textContent = groupe;
            button.addEventListener("click", function () {
                showScreenOrigins(groupe);
            });
            groupButtonsEl.appendChild(button);
        });
    }

    function disableButtonsBriefly() {
        const buttons = document.querySelectorAll(".origin-button, .group-button");
        buttons.forEach(function (button) {
            button.disabled = true;
        });
        window.setTimeout(function () {
            buttons.forEach(function (button) {
                button.disabled = false;
            });
        }, 1000);
    }

    function showError(message) {
        errorMessageEl.textContent = message;
        errorMessageEl.hidden = false;
        window.setTimeout(function () {
            errorMessageEl.hidden = true;
        }, 4000);
    }

    function showConfirmation(originNom, visitId) {
        lastVisitId = visitId;
        confirmationText.textContent = originNom + " enregistré ✓";
        confirmationEl.hidden = false;

        if (confirmationTimeoutId) {
            window.clearTimeout(confirmationTimeoutId);
        }
        confirmationTimeoutId = window.setTimeout(function () {
            confirmationEl.hidden = true;
            lastVisitId = null;
        }, 5000);
    }

    function submitVisit(originCode, precisionLibre) {
        disableButtonsBriefly();

        fetch(createUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ origin_code: originCode, precision_libre: precisionLibre }),
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("request-failed");
                }
                return response.json();
            })
            .then(function (data) {
                showConfirmation(data.origin_nom, data.id);
                showScreenGroups();
            })
            .catch(function () {
                showError("Échec de l'enregistrement. Vérifiez la connexion et réessayez.");
            });
    }

    cancelButton.addEventListener("click", function () {
        if (!lastVisitId) {
            return;
        }
        const url = cancelUrlBase.replace(/0\/annuler\/$/, lastVisitId + "/annuler/");

        fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("request-failed");
                }
                confirmationEl.hidden = true;
                lastVisitId = null;
            })
            .catch(function () {
                showError("Échec de l'annulation. Réessayez.");
            });
    });

    backButton.addEventListener("click", showScreenGroups);

    autreSubmit.addEventListener("click", function () {
        const value = autreInput.value.trim();
        if (!value) {
            return;
        }
        submitVisit("AUTRE", value);
    });

    renderGroups();
})();
