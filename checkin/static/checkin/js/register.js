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

    const screenGroupCount = document.getElementById("screen-group-count");
    const groupCountTitle = document.getElementById("group-count-title");
    const groupCountButtonsEl = document.getElementById("group-count-buttons");
    const backToOriginsButton = document.getElementById("back-to-origins-button");

    const MAX_GROUP_COUNT = 10;

    let confirmationTimeoutId = null;
    let lastVisitIds = [];

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
        screenGroupCount.hidden = true;
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
                if (origin.type === "autre") {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "origin-button";
                    button.textContent = origin.nom;
                    button.addEventListener("click", function () {
                        autreForm.hidden = false;
                        autreInput.value = "";
                        autreInput.focus();
                    });
                    originButtonsEl.appendChild(button);
                    return;
                }

                const label = origin.type === "departement" ? origin.code + " " + origin.nom : origin.nom;

                const unit = document.createElement("div");
                unit.className = "origin-unit";

                const mainButton = document.createElement("button");
                mainButton.type = "button";
                mainButton.className = "origin-button";
                mainButton.textContent = label;
                mainButton.addEventListener("click", function () {
                    submitVisit(origin.code, "", 1);
                });
                unit.appendChild(mainButton);

                const groupButton = document.createElement("button");
                groupButton.type = "button";
                groupButton.className = "origin-group-button";
                groupButton.setAttribute("aria-label", "Enregistrer un groupe pour " + label);
                groupButton.innerHTML =
                    '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">' +
                    '<rect x="-1" y="12" width="12" height="10" rx="5"/>' +
                    '<circle cx="5" cy="8.5" r="3"/>' +
                    '<rect x="13" y="12" width="12" height="10" rx="5"/>' +
                    '<circle cx="19" cy="8.5" r="3"/>' +
                    '<rect x="4" y="10.5" width="16" height="12" rx="6"/>' +
                    '<circle cx="12" cy="7.2" r="3.8"/>' +
                    "</svg>";
                groupButton.addEventListener("click", function () {
                    showScreenGroupCount(origin, label);
                });
                unit.appendChild(groupButton);

                originButtonsEl.appendChild(unit);
            });

        screenGroups.hidden = true;
        screenGroupCount.hidden = true;
        screenOrigins.hidden = false;
    }

    function showScreenGroupCount(origin, label) {
        groupCountTitle.textContent = label;
        groupCountButtonsEl.innerHTML = "";

        for (let count = 1; count <= MAX_GROUP_COUNT; count++) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "origin-button";
            button.textContent = String(count);
            button.addEventListener("click", function () {
                submitVisit(origin.code, "", count);
            });
            groupCountButtonsEl.appendChild(button);
        }

        screenOrigins.hidden = true;
        screenGroupCount.hidden = false;
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
        const buttons = document.querySelectorAll(".origin-button, .group-button, .origin-group-button");
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

    function showConfirmation(originNom, ids, count) {
        lastVisitIds = ids;
        confirmationText.textContent =
            count > 1 ? count + " × " + originNom + " enregistrés ✓" : originNom + " enregistré ✓";
        confirmationEl.hidden = false;

        if (confirmationTimeoutId) {
            window.clearTimeout(confirmationTimeoutId);
        }
        confirmationTimeoutId = window.setTimeout(function () {
            confirmationEl.hidden = true;
            lastVisitIds = [];
        }, 5000);
    }

    function submitVisit(originCode, precisionLibre, count) {
        disableButtonsBriefly();

        fetch(createUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ origin_code: originCode, precision_libre: precisionLibre, count: count }),
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("request-failed");
                }
                return response.json();
            })
            .then(function (data) {
                showConfirmation(data.origin_nom, data.ids, count);
                showScreenGroups();
            })
            .catch(function () {
                showError("Échec de l'enregistrement. Vérifiez la connexion et réessayez.");
            });
    }

    cancelButton.addEventListener("click", function () {
        if (lastVisitIds.length === 0) {
            return;
        }
        const idsToCancel = lastVisitIds;

        Promise.all(
            idsToCancel.map(function (visitId) {
                const url = cancelUrlBase.replace(/0\/annuler\/$/, visitId + "/annuler/");
                return fetch(url, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCsrfToken() },
                }).then(function (response) {
                    if (!response.ok) {
                        throw new Error("request-failed");
                    }
                });
            })
        )
            .then(function () {
                confirmationEl.hidden = true;
                lastVisitIds = [];
            })
            .catch(function () {
                showError("Échec de l'annulation. Réessayez.");
            });
    });

    backButton.addEventListener("click", showScreenGroups);

    backToOriginsButton.addEventListener("click", function () {
        screenGroupCount.hidden = true;
        screenOrigins.hidden = false;
    });

    autreSubmit.addEventListener("click", function () {
        const value = autreInput.value.trim();
        if (!value) {
            return;
        }
        submitVisit("AUTRE", value, 1);
    });

    renderGroups();
})();
