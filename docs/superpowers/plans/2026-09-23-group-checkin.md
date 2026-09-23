# Enregistrement de groupes en un seul écran — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre d'enregistrer plusieurs visiteurs de la même origine (département/DOM-TOM/pays) en une seule action, sans ralentir le cas d'une personne seule.

**Architecture:** Chaque bouton d'origine (sauf « Autre pays ») devient une capsule à deux zones fusionnées : la zone principale garde le comportement actuel (1 tap = 1 personne), une nouvelle zone « groupe » ouvre un écran de sélection du nombre (1 à 10, tap direct = enregistrement immédiat). Côté serveur, `visit_create` accepte un `count` optionnel et crée autant de lignes `Visit` individuelles — aucun changement du modèle de données, aucun impact sur les statistiques/classement/carte.

**Tech Stack:** Django (vue `visit_create`), CSS (tokens existants du système de thème), JavaScript vanilla (`register.js`), pytest.

## Global Constraints

- Aucune nouvelle couleur codée en dur — tout le nouveau CSS consomme les tokens existants (`--color-accent-end`, `--radius-md`, `--shadow-button`, etc.).
- Aucun changement du modèle `Visit` — chaque personne reste une ligne distincte, créée via `Visit.objects.create()` en boucle (pas `bulk_create`, pour garantir `auto_now_add` sur `horodatage`).
- `visit_create` reste rétrocompatible : un appel sans `count` doit produire exactement la même réponse qu'aujourd'hui côté champ `id` (les tests existants de `test_views_visit_api.py` ne doivent pas être modifiés).
- Le sélecteur de nombre va de 1 à 10 uniquement — pas de gestion "10+".
- L'origine `autre` (saisie libre) n'est pas concernée par ce travail — elle garde son bouton unique actuel.
- Pas de nouvelle dépendance JS/CDN. Pas de framework, pas de build step — cohérent avec le reste du projet.
- Aucune régression sur la suite de tests existante (98 tests avant ce plan).

---

### Task 1: `visit_create` accepte un `count` (création groupée côté serveur)

**Files:**
- Modify: `checkin/views.py`
- Test: `checkin/tests/test_views_visit_api.py`

**Interfaces:**
- Consumes: rien de nouveau (vue existante).
- Produces: `visit_create` accepte désormais `count` (entier, 1-10, défaut 1) dans le corps JSON. Réponse : `{"id": <premier id>, "ids": [<tous les ids>], "origin_nom": "..."}` — le champ `id` reste identique au comportement actuel, `ids` est nouveau et sera consommé par Task 2.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views_visit_api.py`, juste après `test_visit_create_records_a_visit` :

```python
@pytest.mark.django_db
def test_visit_create_with_count_creates_multiple_visits(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.get(code="75")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_create", kwargs={"festival_slug": festival.slug}),
        data=json.dumps({"origin_code": "75", "count": 5}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["ids"]) == 5
    assert data["id"] == data["ids"][0]
    assert len(set(data["ids"])) == 5
    assert Visit.objects.filter(origin=origin).count() == 5


@pytest.mark.django_db
def test_visit_create_without_count_still_returns_matching_id_and_ids(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_create", kwargs={"festival_slug": festival.slug}),
        data=json.dumps({"origin_code": "75"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ids"] == [data["id"]]


@pytest.mark.django_db
@pytest.mark.parametrize("bad_count", [0, 11, -1, "abc", 3.5, True])
def test_visit_create_rejects_invalid_count(client, django_user_model, bad_count):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_create", kwargs={"festival_slug": festival.slug}),
        data=json.dumps({"origin_code": "75", "count": bad_count}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert Visit.objects.count() == 0
```

- [ ] **Step 2: Lancer les tests pour vérifier qu'ils échouent**

Run: `.venv/Scripts/python.exe -m pytest checkin/tests/test_views_visit_api.py -v`
Expected: les 3 nouveaux tests échouent (`test_visit_create_with_count_creates_multiple_visits` avec un `KeyError` sur `"ids"`, `test_visit_create_rejects_invalid_count` avec un `assert 201 == 400`), les tests existants passent toujours.

- [ ] **Step 3: Implémenter le support de `count` dans `visit_create`**

Dans `checkin/views.py`, remplacer la fonction `visit_create` (actuellement lignes ~87-111) par :

```python
def visit_create(request, festival_slug):
    edition = get_active_edition(request.festival)
    if edition is None:
        return JsonResponse({"error": "Aucune édition en cours."}, status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Requête invalide."}, status=400)

    origin_code = payload.get("origin_code")
    origin = Origin.objects.filter(code=origin_code).first()
    if origin is None:
        return JsonResponse({"error": "Origine inconnue."}, status=400)

    count = payload.get("count", 1)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > 10:
        return JsonResponse({"error": "Nombre invalide."}, status=400)

    precision_libre = payload.get("precision_libre") or ""

    visits = [
        Visit.objects.create(
            edition=edition,
            origin=origin,
            enregistre_par=request.user,
            precision_libre=precision_libre,
        )
        for _ in range(count)
    ]

    return JsonResponse(
        {"id": visits[0].id, "ids": [visit.id for visit in visits], "origin_nom": origin.nom},
        status=201,
    )
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv/Scripts/python.exe -m pytest checkin/tests/test_views_visit_api.py -v`
Expected: tous les tests de ce fichier passent, y compris les 3 nouveaux et les 5 existants (aucune régression).

- [ ] **Step 5: Lancer la suite complète**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: aucune régression sur l'ensemble de la suite.

- [ ] **Step 6: Commit**

```bash
git add checkin/views.py checkin/tests/test_views_visit_api.py
git commit -m "feat: permet a visit_create d'enregistrer plusieurs visites en une requete"
```

---

### Task 2: Bouton fusionné, sélecteur de nombre et annulation groupée (frontend)

**Files:**
- Modify: `checkin/static/checkin/css/base.css`
- Modify: `checkin/templates/checkin/register.html`
- Modify: `checkin/static/checkin/js/register.js`

**Interfaces:**
- Consumes: `visit_create` avec `count` et réponse `{id, ids, origin_nom}` (Task 1). `visit_cancel` existant, inchangé, appelé une fois par id.
- Produces: rien de consommé par une tâche ultérieure — dernière tâche du plan.

- [ ] **Step 1: Ajouter les styles CSS**

Dans `checkin/static/checkin/css/base.css`, juste après le bloc `.group-button:disabled, .origin-button:disabled { ... }` (avant la règle `#back-button`), ajouter :

```css
.origin-unit {
    display: flex;
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-button);
}

.origin-unit .origin-button {
    flex: 1;
    border-radius: 0;
    box-shadow: none;
    font-size: 1.15rem;
}

.origin-group-button {
    width: 46px;
    min-height: 88px;
    border: none;
    border-left: 1px solid rgba(255, 255, 255, 0.25);
    background: var(--color-accent-end);
    color: var(--color-accent-text);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    cursor: pointer;
    touch-action: manipulation;
    transition: var(--transition-interactive);
}

.origin-group-button:active {
    transform: scale(0.96);
}

.origin-group-button:disabled {
    background: var(--color-surface);
    color: var(--color-text-muted);
    cursor: not-allowed;
}
```

Remplacer la règle `#back-button { ... }` par (ajoute `.back-button` comme sélecteur alternatif, pour le nouveau bouton retour de l'écran de sélection du nombre — mêmes styles, id différent) :

```css
#back-button,
.back-button {
    min-height: 56px;
    font-size: 1.1rem;
    margin: 1rem;
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: var(--radius-sm);
    background-color: var(--color-surface);
    color: var(--color-text);
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: var(--transition-theme);
}
```

- [ ] **Step 2: Ajouter l'écran de sélection du nombre à `register.html`**

Dans `checkin/templates/checkin/register.html`, remplacer :

```html
<section id="screen-origins" hidden>
    <button type="button" id="back-button">← Retour</button>
    <h2 id="selected-group-title"></h2>
    <div class="button-grid" id="origin-buttons"></div>
    <div id="autre-form" hidden>
        <input type="text" id="autre-input" placeholder="Précisez le pays">
        <button type="button" id="autre-submit">Valider</button>
    </div>
</section>
```

par :

```html
<section id="screen-origins" hidden>
    <button type="button" id="back-button">← Retour</button>
    <h2 id="selected-group-title"></h2>
    <div class="button-grid" id="origin-buttons"></div>
    <div id="autre-form" hidden>
        <input type="text" id="autre-input" placeholder="Précisez le pays">
        <button type="button" id="autre-submit">Valider</button>
    </div>
</section>

<section id="screen-group-count" hidden>
    <button type="button" class="back-button" id="back-to-origins-button">← Retour</button>
    <h2 id="group-count-title"></h2>
    <div class="button-grid" id="group-count-buttons"></div>
</section>
```

(Seul changement du fichier : la nouvelle section `#screen-group-count`, ajoutée entre `#screen-origins` et le `<script id="origins-data">`. Le reste du fichier — y compris le `{% block back_link %}` déjà présent — est inchangé.)

- [ ] **Step 3: Réécrire `register.js`**

Remplacer l'intégralité de `checkin/static/checkin/js/register.js` par :

```javascript
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
```

- [ ] **Step 4: Lancer la suite de tests complète**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: aucune régression (ce fichier n'est pas couvert par pytest, mais s'assurer qu'aucun autre test ne casse).

- [ ] **Step 5: Vérification manuelle (Playwright)**

Avec un compte bénévole ou organisateur sur une édition active, dérouler dans un navigateur (via les outils `mcp__playwright__*`) :

1. Écran de connexion → aller sur Enregistrement → choisir un groupe → vérifier que chaque département affiche bien la capsule à deux zones (bouton principal + bouton 👥 avec l'icône 3 personnes, séparés par un fin trait).
2. Taper sur la zone principale d'un département → vérifier l'enregistrement immédiat d'une personne (comportement inchangé) et la bannière « *Département* enregistré ✓ ».
3. Taper sur la zone 👥 d'un autre département → vérifier l'écran « combien de personnes » avec les boutons 1 à 10 → taper sur un nombre (ex: 5) → vérifier le retour immédiat à l'écran des groupes et la bannière « 5 × *Département* enregistrés ✓ ».
4. Taper « Annuler » sur cette bannière de groupe → vérifier que les 5 visites ont bien été supprimées (recharger la page stats ou vérifier via l'API/admin que le compteur ne les inclut plus).
5. Depuis l'écran « combien de personnes », taper « ← Retour » → vérifier le retour à l'écran des départements sans qu'aucune visite ne soit créée.
6. Vérifier que l'origine « Autre pays » n'a toujours qu'un seul bouton (pas de zone groupe) et fonctionne comme avant (saisie du nom + Valider = 1 personne).
7. Vérifier le rendu dans les deux thèmes (clair/sombre) : la zone 👥 doit rester lisible (fond bleu plein, pas confondu avec le fond de page) dans les deux cas.
8. Vérifier la console du navigateur : aucune erreur JS sur ces écrans.

- [ ] **Step 6: Commit**

```bash
git add checkin/static/checkin/css/base.css checkin/templates/checkin/register.html checkin/static/checkin/js/register.js
git commit -m "feat: ajoute l'enregistrement de groupe par origine (bouton fusionne + selecteur de nombre)"
```

---
