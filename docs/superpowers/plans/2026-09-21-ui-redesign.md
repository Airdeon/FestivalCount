# Refonte visuelle de l'interface (thèmes clair/sombre) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le CSS minimal actuel par un vrai système de design (tokens de couleurs, ombres, dégradés, transitions) avec bascule de thème clair/sombre persistante, appliqué à toute l'application (Django, projet `festivalcount` / app `checkin`).

**Architecture:** Variables CSS (`custom properties`) définies sur `:root` et redéfinies selon l'attribut `data-theme` porté par `<html>` (`dark` par défaut). Un script inline anti-flash lit la préférence enregistrée en `localStorage` avant le premier rendu ; un bouton dans `base.html` bascule le thème et notifie le reste de la page (Chart.js, carte SVG) via un évènement `themechange`. Travail purement visuel — pas de nouveau modèle, pas de nouvelle route, une seule vue modifiée (calcul d'un pourcentage d'affichage).

**Tech Stack:** Identique au projet existant — Django 6.1.1, Python 3.14, pytest + pytest-django, CSS vanilla (custom properties, pas de framework), JavaScript vanilla, Chart.js (déjà vendored).

## Global Constraints

- Aucune couleur codée en dur en dehors de la définition des tokens (spec : Système de design tokens) — tout le CSS applicatif consomme les variables `--color-*`/`--shadow-*`/`--radius-*`.
- Thème `dark` par défaut ; bascule vers `light` via un bouton, persistée en `localStorage`, restaurée avant le premier rendu pour éviter un flash (spec : Mécanisme de bascule de thème).
- Bouton de bascule et bouton de déconnexion visibles uniquement pour un utilisateur connecté (spec : Mécanisme de bascule de thème).
- Bannière de confirmation « succès » reste verte dans les deux thèmes (spec : maquettes validées).
- Carte de France et graphiques Chart.js lisent leurs couleurs depuis les variables CSS calculées (`getComputedStyle`), pas de duplication de couleurs en JS (spec : Page de statistiques).
- Pas de nouvelle dépendance JS/CDN — tout reste vendored localement, cohérent avec l'architecture existante.
- Aucune régression sur la suite de tests existante (spec : Tests — travail purement visuel, pas de nouveaux tests pytest hormis le calcul de pourcentage du classement).

---

### Task 1: Système de tokens CSS + bascule de thème

**Files:**
- Modify: `checkin/static/checkin/css/base.css`
- Modify: `checkin/templates/checkin/base.html`
- Create: `checkin/static/checkin/js/theme.js`

**Interfaces:**
- Consumes: rien (fondation du système, première tâche).
- Produces: variables CSS `--color-bg`, `--color-text`, `--color-text-muted`, `--color-surface`, `--color-surface-border`, `--color-accent-start`, `--color-accent-end`, `--color-accent-text`, `--color-accent-soft-start`, `--color-accent-soft-end`, `--color-accent-solid`, `--color-success-bg-start`, `--color-success-bg-end`, `--color-success-text`, `--color-error-bg`, `--color-error-text`, `--color-map-empty`, `--color-map-low`, `--color-map-high`, `--shadow-container`, `--shadow-card`, `--shadow-button`, `--radius-lg`, `--radius-md`, `--radius-sm`, `--transition-theme`, `--transition-interactive` (consommées par les tâches suivantes). Évènement DOM `themechange` (`document.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }))`), consommé par les Tasks 2 et 3 pour re-thémer la carte et les graphiques sans recharger la page.

- [ ] **Step 1: Réécrire `checkin/static/checkin/css/base.css`**

Remplacer l'intégralité du fichier par :

```css
* {
    box-sizing: border-box;
}

[hidden] {
    display: none !important;
}

:root,
[data-theme="dark"] {
    --color-bg: radial-gradient(circle at 20% -10%, #1f2937 0%, #0b0d14 55%);
    --color-text: #e5e7eb;
    --color-text-muted: #9ca3af;

    --color-surface: rgba(255, 255, 255, 0.04);
    --color-surface-border: rgba(255, 255, 255, 0.08);

    --color-accent-start: #3b82f6;
    --color-accent-end: #1d4ed8;
    --color-accent-text: #ffffff;
    --color-accent-soft-start: rgba(59, 130, 246, 0.18);
    --color-accent-soft-end: rgba(29, 78, 216, 0.08);
    --color-accent-solid: #60a5fa;

    --color-success-bg-start: #0f5132;
    --color-success-bg-end: #0a3622;
    --color-success-text: #86efac;

    --color-error-bg: #611a15;
    --color-error-text: #ffffff;

    --color-map-empty: #1f2937;
    --color-map-low: #1e40af;
    --color-map-high: #60a5fa;

    --shadow-container: 0 20px 50px -20px rgba(0, 0, 0, 0.5);
    --shadow-card: 0 8px 18px -12px rgba(0, 0, 0, 0.5);
    --shadow-button: 0 10px 20px -10px rgba(37, 99, 235, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

[data-theme="light"] {
    --color-bg: #eef1f6;
    --color-text: #0f172a;
    --color-text-muted: #64748b;

    --color-surface: #ffffff;
    --color-surface-border: rgba(15, 23, 42, 0.08);

    --color-accent-start: #3b82f6;
    --color-accent-end: #1d4ed8;
    --color-accent-text: #ffffff;
    --color-accent-soft-start: rgba(59, 130, 246, 0.1);
    --color-accent-soft-end: rgba(96, 165, 250, 0.04);
    --color-accent-solid: #1d4ed8;

    --color-success-bg-start: #dcfce7;
    --color-success-bg-end: #bbf7d0;
    --color-success-text: #14532d;

    --color-error-bg: #fdecea;
    --color-error-text: #611a15;

    --color-map-empty: #e2e8f0;
    --color-map-low: #93c5fd;
    --color-map-high: #1d4ed8;

    --shadow-container: 0 16px 40px -20px rgba(15, 23, 42, 0.2);
    --shadow-card: 0 8px 18px -12px rgba(15, 23, 42, 0.18);
    --shadow-button: 0 10px 20px -10px rgba(37, 99, 235, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

:root {
    --radius-lg: 20px;
    --radius-md: 14px;
    --radius-sm: 10px;
    --transition-theme: background-color 0.35s ease, color 0.35s ease, border-color 0.35s ease;
    --transition-interactive: transform 0.15s ease, box-shadow 0.25s ease;
}

body {
    margin: 0;
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
    min-height: 100vh;
    transition: var(--transition-theme);
}

.theme-toggle {
    position: fixed;
    top: 0.75rem;
    right: 0.75rem;
    z-index: 10;
    border: none;
    border-radius: 999px;
    width: 44px;
    height: 44px;
    font-size: 1.1rem;
    cursor: pointer;
    background: var(--color-surface);
    color: var(--color-accent-solid);
    box-shadow: var(--shadow-card);
    transition: var(--transition-theme), transform 0.15s ease;
}

.theme-toggle:active {
    transform: scale(0.92);
}

.logout-form {
    position: fixed;
    top: 0.75rem;
    right: 4.25rem;
    z-index: 10;
}

.logout-form button {
    border: none;
    border-radius: var(--radius-sm);
    padding: 0.6rem 1rem;
    background: var(--color-surface);
    color: var(--color-text);
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: var(--transition-theme);
}

main {
    padding-top: 3.5rem;
}

.messages {
    list-style: none;
    margin: 0;
    padding: 0;
}

.message {
    padding: 0.75rem 1rem;
    text-align: center;
}

.message--error {
    background-color: var(--color-error-bg);
    color: var(--color-error-text);
}

.message--success {
    background: linear-gradient(135deg, var(--color-success-bg-start), var(--color-success-bg-end));
    color: var(--color-success-text);
}

.message--info {
    background-color: var(--color-surface);
    color: var(--color-text);
}

.no-active-edition {
    text-align: center;
    font-size: 1.5rem;
    padding: 3rem 1rem;
    color: var(--color-text-muted);
}

.button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
    padding: 1rem;
}

.group-button,
.origin-button {
    min-height: 88px;
    font-size: 1.25rem;
    font-weight: 700;
    border: none;
    border-radius: var(--radius-md);
    background: linear-gradient(160deg, var(--color-accent-start), var(--color-accent-end));
    color: var(--color-accent-text);
    cursor: pointer;
    padding: 0.5rem;
    touch-action: manipulation;
    box-shadow: var(--shadow-button);
    transition: var(--transition-interactive);
}

.group-button:active,
.origin-button:active {
    transform: scale(0.96);
}

.group-button:disabled,
.origin-button:disabled {
    background: var(--color-surface);
    color: var(--color-text-muted);
    box-shadow: none;
    cursor: not-allowed;
}

#back-button {
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

.confirmation {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background: linear-gradient(135deg, var(--color-success-bg-start), var(--color-success-bg-end));
    color: var(--color-success-text);
    padding: 1rem;
    font-size: 1.1rem;
}

.confirmation button {
    min-height: 48px;
    padding: 0.5rem 1.25rem;
    border: none;
    border-radius: var(--radius-sm);
    background-color: rgba(255, 255, 255, 0.9);
    color: var(--color-success-bg-end);
    font-weight: 700;
    cursor: pointer;
}

.error-message {
    background-color: var(--color-error-bg);
    color: var(--color-error-text);
    padding: 1rem;
    text-align: center;
    font-size: 1.1rem;
}

#autre-form {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
}

#autre-form input {
    flex: 1;
    font-size: 1.1rem;
    padding: 0.75rem;
    border: 1px solid var(--color-surface-border);
    border-radius: var(--radius-sm);
    background-color: var(--color-surface);
    color: var(--color-text);
}

#autre-form button {
    min-height: 48px;
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: var(--radius-sm);
    background: linear-gradient(160deg, var(--color-accent-start), var(--color-accent-end));
    color: var(--color-accent-text);
    font-weight: 700;
    cursor: pointer;
}

@media (min-width: 768px) {
    .button-grid {
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    }
}
```

- [ ] **Step 2: Ajouter le script anti-flash et le bouton de thème dans `checkin/templates/checkin/base.html`**

Remplacer le contenu du fichier par :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script>
        (function () {
            try {
                var stored = localStorage.getItem("theme");
                if (stored === "light" || stored === "dark") {
                    document.documentElement.setAttribute("data-theme", stored);
                }
            } catch (e) {
                // localStorage indisponible (navigation privee stricte) : reste sur le theme par defaut.
            }
        })();
    </script>
    <title>{% block title %}Festival Count{% endblock %}</title>
    <link rel="stylesheet" href="{% load static %}{% static 'checkin/css/base.css' %}">
</head>
<body>
    {% if messages %}
    <ul class="messages">
        {% for message in messages %}
        <li class="message message--{{ message.tags }}">{{ message }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    {% if user.is_authenticated %}
    <button type="button" class="theme-toggle" id="themeToggle" aria-label="Changer de theme">☀️</button>
    <form method="post" action="{% url 'checkin:logout' %}" class="logout-form">
        {% csrf_token %}
        <button type="submit">Se déconnecter</button>
    </form>
    {% endif %}
    <main>
        {% block content %}{% endblock %}
    </main>
    <script src="{% static 'checkin/js/theme.js' %}" defer></script>
</body>
</html>
```

- [ ] **Step 3: Créer `checkin/static/checkin/js/theme.js`**

```javascript
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
```

- [ ] **Step 4: Vérifier l'absence de régression**

Run: `.venv/Scripts/python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: tous les tests passent (aucune assertion HTML cassée — le bouton de thème et le script ajoutés ne touchent aucun texte/attribut vérifié par les tests existants).

- [ ] **Step 5: Vérification manuelle**

Run: `.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8001 --noreload`

Se connecter avec un compte de test, ouvrir n'importe quelle page authentifiée.
Expected : fond sombre par défaut, bouton ☀️ en haut à droite à côté du bouton de déconnexion (repositionné). Cliquer sur ☀️ → passage en thème clair (fond gris doux), icône devient 🌙. Recharger la page → le thème clair est conservé (pas de flash de fond sombre avant le clair). Ouvrir les outils de dev, exécuter `localStorage.clear()`, recharger → retour au sombre par défaut.

- [ ] **Step 6: Commit**

```bash
git add checkin/static/checkin/css/base.css checkin/templates/checkin/base.html checkin/static/checkin/js/theme.js
git commit -m "feat: ajoute le systeme de tokens CSS et la bascule de theme clair/sombre"
```

---

### Task 2: Cartes KPI et classement en barres sur la page de statistiques

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/templates/checkin/stats.html`
- Modify: `checkin/static/checkin/css/base.css`
- Modify: `checkin/tests/test_views_stats.py`

**Interfaces:**
- Consumes: tokens CSS de la Task 1 (`--color-surface`, `--shadow-card`, `--color-accent-*`, `--radius-*`).
- Produces: chaque entrée de `ranking` passée au template contient désormais une clé `pourcentage` (int, 0-100) en plus de `origin__code`/`origin__nom`/`nombre` — ne change pas la signature de `checkin.stats.get_ranking()` elle-même (le calcul est fait dans la vue).

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à `checkin/tests/test_views_stats.py` (le fichier importe déjà `pytest`, `reverse`, `Edition`, `Festival`, `Membership`, `Origin`, `Visit`) :

```python
@pytest.mark.django_db
def test_stats_ranking_includes_percentage_relative_to_max(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    paris = Origin.objects.get(code="75")
    rhone = Origin.objects.get(code="69")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "width: 100%" in content
    assert "width: 50%" in content
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `.venv/Scripts/python.exe -m pytest checkin/tests/test_views_stats.py -v -k percentage`
Expected: FAIL — `assert "width: 100%" in content` échoue (le template ne rend pas encore de barres)

- [ ] **Step 3: Calculer le pourcentage dans la vue**

Dans `checkin/views.py`, remplacer le corps de la fonction `stats` :

```python
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def stats(request, festival_slug):
    editions = request.festival.editions.all()
    active_edition = get_active_edition(request.festival)

    edition_id = request.GET.get("edition")
    edition = editions.filter(id=edition_id).first() if edition_id else active_edition
    if edition is None:
        edition = editions.first()

    context = {"editions": editions, "selected_edition": edition}
    if edition is not None:
        context["key_figures"] = get_key_figures(edition)
        ranking = get_ranking(edition)
        max_count = max((row["nombre"] for row in ranking), default=0)
        for row in ranking:
            row["pourcentage"] = round((row["nombre"] / max_count) * 100) if max_count else 0
        context["ranking"] = ranking
        context["hourly_evolution"] = get_hourly_evolution(edition)
        context["is_current_edition"] = edition == active_edition

    return render(request, "checkin/stats.html", context)
```

- [ ] **Step 4: Restructurer le template**

Remplacer le contenu de `checkin/templates/checkin/stats.html` par :

```html
{% extends "checkin/base.html" %}
{% load static %}
{% block title %}Statistiques — {{ request.festival.nom }}{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }} — Statistiques</h1>

{% if not editions %}
<p>Aucune édition pour ce festival.</p>
{% else %}
<form method="get" id="edition-selector-form" class="edition-selector">
    <label for="edition-selector">Édition :</label>
    <select name="edition" id="edition-selector" onchange="this.form.submit()">
        {% for e in editions %}
        <option value="{{ e.id }}" {% if selected_edition and e.id == selected_edition.id %}selected{% endif %}>{{ e.nom }}</option>
        {% endfor %}
    </select>
</form>

{% if selected_edition %}
<section id="key-figures"
         class="kpi-row"
         data-total="{{ key_figures.total_visiteurs }}"
         data-departements="{{ key_figures.nombre_departements }}"
         data-pays="{{ key_figures.nombre_pays }}"
         data-stats-data-url="{% url 'checkin:stats_data' festival_slug=request.festival.slug %}"
         data-edition-id="{{ selected_edition.id }}"
         data-is-current="{{ is_current_edition|yesno:'true,false' }}">
    <div class="kpi-card">
        <div class="kpi-value" id="total-visiteurs">{{ key_figures.total_visiteurs }}</div>
        <div class="kpi-label">Visiteurs</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value" id="total-departements">{{ key_figures.nombre_departements }}</div>
        <div class="kpi-label">Départements</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value" id="total-pays">{{ key_figures.nombre_pays }}</div>
        <div class="kpi-label">Pays</div>
    </div>
</section>

<div class="panel">
    <h2 class="panel-title">Classement</h2>
    {% for row in ranking %}
    <div class="bar-row">
        <span class="bar-label">{{ row.origin__code }} — {{ row.origin__nom }}</span>
        <div class="bar-track"><div class="bar-fill" style="width: {{ row.pourcentage }}%"></div></div>
        <span class="bar-count">{{ row.nombre }}</span>
    </div>
    {% endfor %}
</div>

<div class="panel">
    <h2 class="panel-title">Évolution</h2>
    <canvas id="ranking-chart" height="220"></canvas>
    <canvas id="evolution-chart" height="220"></canvas>
</div>

<div class="panel">
    <h2 class="panel-title">Carte de France</h2>
    <div id="map-container" data-svg-url="{% static 'checkin/svg/france-departements.svg' %}"></div>
</div>

{{ ranking|json_script:"ranking-data" }}
{{ hourly_evolution|json_script:"evolution-data" }}

<script src="{% static 'checkin/js/vendor/chart.umd.min.js' %}"></script>
<script src="{% static 'checkin/js/map.js' %}" defer></script>
<script src="{% static 'checkin/js/stats.js' %}" defer></script>
{% endif %}
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Ajouter les styles des cartes KPI et du panneau de classement**

Ajouter à la fin de `checkin/static/checkin/css/base.css` :

```css
.edition-selector {
    padding: 1rem;
}

.edition-selector select {
    font-size: 1rem;
    padding: 0.5rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-surface-border);
    background-color: var(--color-surface);
    color: var(--color-text);
}

.kpi-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
    padding: 0 1rem 1rem 1rem;
}

.kpi-card {
    border-radius: var(--radius-md);
    padding: 1rem 0.5rem;
    text-align: center;
    background: linear-gradient(160deg, var(--color-accent-soft-start), var(--color-accent-soft-end));
    box-shadow: var(--shadow-card);
    transition: var(--transition-theme);
}

.kpi-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--color-accent-solid);
}

.kpi-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-text-muted);
    margin-top: 0.25rem;
}

.panel {
    border-radius: var(--radius-md);
    padding: 1rem;
    margin: 0 1rem 1rem 1rem;
    background-color: var(--color-surface);
    box-shadow: var(--shadow-card);
    transition: var(--transition-theme);
}

.panel-title {
    margin: 0 0 0.75rem 0;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-text-muted);
}

.bar-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}

.bar-label {
    width: 40%;
    color: var(--color-text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.bar-track {
    flex: 1;
    height: 10px;
    border-radius: 999px;
    background-color: var(--color-surface-border);
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--color-accent-start), var(--color-accent-solid));
}

.bar-count {
    width: 2rem;
    text-align: right;
    color: var(--color-text);
    font-weight: 700;
}
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `.venv/Scripts/python.exe -m pytest checkin/tests/test_views_stats.py -v`
Expected: tous les tests du fichier passent, y compris le nouveau.

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: aucune régression sur l'ensemble de la suite (88 tests avant cette tâche, 89 après).

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/templates/checkin/stats.html checkin/static/checkin/css/base.css checkin/tests/test_views_stats.py
git commit -m "feat: ajoute les cartes KPI et le classement en barres sur la page statistiques"
```

---

### Task 3: Carte et graphiques adaptés au thème

**Files:**
- Modify: `checkin/static/checkin/js/map.js`
- Modify: `checkin/static/checkin/js/stats.js`

**Interfaces:**
- Consumes: variables CSS `--color-map-empty`, `--color-map-low`, `--color-map-high`, `--color-surface-border`, `--color-text`, `--color-accent-solid` (Task 1) ; évènement `themechange` (Task 1).
- Produces: aucune nouvelle interface consommée par d'autres tâches — dernière couche de theming.

- [ ] **Step 1: Rendre `map.js` sensible au thème**

Remplacer le contenu de `checkin/static/checkin/js/map.js` par :

```javascript
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
```

- [ ] **Step 2: Rendre `stats.js` sensible au thème**

Remplacer le contenu de `checkin/static/checkin/js/stats.js` par :

```javascript
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
```

- [ ] **Step 3: Vérifier l'absence de régression**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: aucune régression (ces fichiers ne sont pas couverts par des tests pytest — vérification qu'aucun test HTML ne référence leur contenu).

- [ ] **Step 4: Vérification manuelle**

Run: `.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8001 --noreload`

Se connecter en tant qu'organisateur d'un festival ayant des `Visit` enregistrées sur plusieurs départements, ouvrir la page statistiques. Ouvrir la console du navigateur : aucune erreur. Vérifier que le graphique en barres, le graphique en ligne, et la carte utilisent des couleurs cohérentes avec le thème sombre actif. Cliquer sur le bouton de thème (☀️) : la carte et les deux graphiques changent de couleur immédiatement, sans recharger la page.

- [ ] **Step 5: Commit**

```bash
git add checkin/static/checkin/js/map.js checkin/static/checkin/js/stats.js
git commit -m "feat: adapte la carte et les graphiques Chart.js au theme actif"
```

---

### Task 4: Styles cohérents pour les pages secondaires

**Files:**
- Modify: `checkin/static/checkin/css/base.css`
- Modify: `checkin/templates/registration/login.html`
- Modify: `checkin/templates/checkin/signup.html`
- Modify: `checkin/templates/checkin/festival_create.html`
- Modify: `checkin/templates/checkin/select_festival.html`
- Modify: `checkin/templates/checkin/festival_search.html`
- Modify: `checkin/templates/checkin/edition_list.html`
- Modify: `checkin/templates/checkin/volunteer_list.html`

**Interfaces:**
- Consumes: tokens CSS de la Task 1.
- Produces: classes `.page-card` (formulaire centré unique), `.page-content` (conteneur de page mélangeant liste et liens), `.simple-list` (liste de cartes), `.form-section` (bloc de formulaire secondaire au sein d'une page), consommées uniquement par les templates de cette tâche.

- [ ] **Step 1: Ajouter les classes génériques**

Ajouter à la fin de `checkin/static/checkin/css/base.css` :

```css
.page-card {
    max-width: 480px;
    margin: 1.5rem auto;
    padding: 1.5rem;
    border-radius: var(--radius-lg);
    background-color: var(--color-surface);
    box-shadow: var(--shadow-container);
}

.page-card h1 {
    margin-top: 0;
}

.page-card input,
.page-card select {
    width: 100%;
    font-size: 1rem;
    padding: 0.65rem 0.75rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-surface-border);
    background-color: var(--color-bg);
    color: var(--color-text);
}

.page-card button[type="submit"] {
    width: 100%;
    min-height: 48px;
    border: none;
    border-radius: var(--radius-sm);
    background: linear-gradient(160deg, var(--color-accent-start), var(--color-accent-end));
    color: var(--color-accent-text);
    font-weight: 700;
    font-size: 1rem;
    cursor: pointer;
    box-shadow: var(--shadow-button);
}

.page-card a {
    color: var(--color-accent-solid);
}

.page-content {
    max-width: 480px;
    margin: 1.5rem auto;
    padding: 0 1rem;
}

.page-content a {
    color: var(--color-accent-solid);
}

.simple-list {
    list-style: none;
    margin: 0 0 1rem 0;
    padding: 0;
}

.simple-list li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: var(--radius-md);
    background-color: var(--color-surface);
    box-shadow: var(--shadow-card);
}

.simple-list a {
    color: var(--color-text);
    text-decoration: none;
    flex: 1;
}

.simple-list button {
    border: none;
    border-radius: var(--radius-sm);
    padding: 0.5rem 0.85rem;
    background-color: var(--color-surface-border);
    color: var(--color-text);
    cursor: pointer;
    font-size: 0.85rem;
    flex-shrink: 0;
}

.form-section {
    border-radius: var(--radius-md);
    padding: 1rem;
    margin-bottom: 1rem;
    background-color: var(--color-surface);
    box-shadow: var(--shadow-card);
}

.form-section input,
.form-section select {
    width: 100%;
    font-size: 1rem;
    padding: 0.6rem 0.75rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-surface-border);
    background-color: var(--color-bg);
    color: var(--color-text);
    margin-bottom: 0.5rem;
}

.form-section button[type="submit"] {
    min-height: 44px;
    padding: 0 1.25rem;
    border: none;
    border-radius: var(--radius-sm);
    background: linear-gradient(160deg, var(--color-accent-start), var(--color-accent-end));
    color: var(--color-accent-text);
    font-weight: 700;
    cursor: pointer;
}
```

- [ ] **Step 2: Appliquer `.page-card` aux formulaires simples**

Remplacer le contenu de `checkin/templates/registration/login.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Connexion — Festival Count{% endblock %}
{% block content %}
<div class="page-card">
    <h1>Connexion</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Se connecter</button>
    </form>
    <p><a href="{% url 'checkin:signup' %}">Créer un compte</a></p>
</div>
{% endblock %}
```

Remplacer le contenu de `checkin/templates/checkin/signup.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un compte — Festival Count{% endblock %}
{% block content %}
<div class="page-card">
    <h1>Créer un compte</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Créer mon compte</button>
    </form>
</div>
{% endblock %}
```

Remplacer le contenu de `checkin/templates/checkin/festival_create.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un festival — Festival Count{% endblock %}
{% block content %}
<div class="page-card">
    <h1>Créer un festival</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Créer</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 3: Appliquer `.page-content`/`.simple-list` aux pages de liste**

Remplacer le contenu de `checkin/templates/checkin/select_festival.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Mes festivals — Festival Count{% endblock %}
{% block content %}
<div class="page-content">
<h1>Mes festivals</h1>
{% if memberships %}
<ul class="simple-list">
    {% for membership in memberships %}
    <li>
        <a href="{% if membership.role == 'organisateur' %}{% url 'checkin:stats' festival_slug=membership.festival.slug %}{% else %}{% url 'checkin:register' festival_slug=membership.festival.slug %}{% endif %}">
            {{ membership.festival.nom }} — {{ membership.get_role_display }}
        </a>
    </li>
    {% endfor %}
</ul>
{% else %}
<p>Vous n'avez accès à aucun festival pour le moment.</p>
{% endif %}

<p><a href="{% url 'checkin:festival_create' %}">Créer un festival</a></p>
<p><a href="{% url 'checkin:festival_search' %}">Rejoindre un festival</a></p>
</div>
{% endblock %}
```

Remplacer le contenu de `checkin/templates/checkin/festival_search.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Rejoindre un festival — Festival Count{% endblock %}
{% block content %}
<div class="page-content">
<h1>Rejoindre un festival</h1>
<div class="form-section">
    <form method="get">
        <input type="text" name="q" value="{{ query }}" placeholder="Nom du festival">
        <button type="submit">Rechercher</button>
    </form>
</div>

<ul class="simple-list">
    {% for result in results %}
    <li>
        <span>{{ result.festival.nom }}</span>
        {% if result.pending %}
        <span>Demande envoyée</span>
        {% else %}
        <form method="post" action="{% url 'checkin:membership_request_create' festival_slug=result.festival.slug %}">
            {% csrf_token %}
            <input type="hidden" name="q" value="{{ query }}">
            <button type="submit">Demander à rejoindre</button>
        </form>
        {% endif %}
    </li>
    {% endfor %}
</ul>
</div>
{% endblock %}
```

Remplacer le contenu de `checkin/templates/checkin/edition_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Éditions — {{ request.festival.nom }}{% endblock %}
{% block content %}
<div class="page-content">
<h1>{{ request.festival.nom }} — Éditions</h1>

<ul class="simple-list">
    {% for edition in editions %}
    <li>
        <span>{{ edition.nom }} ({{ edition.date_debut }} – {{ edition.date_fin }}){% if edition.est_active %} — en cours{% endif %}</span>
    </li>
    {% endfor %}
</ul>

<div class="form-section">
    <h2 class="panel-title">Créer une nouvelle édition</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Créer</button>
    </form>
</div>
</div>
{% endblock %}
```

Remplacer le contenu de `checkin/templates/checkin/volunteer_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Bénévoles — {{ request.festival.nom }}{% endblock %}
{% block content %}
<div class="page-content">
<h1>{{ request.festival.nom }} — Bénévoles</h1>

<h2 class="panel-title">Demandes en attente</h2>
<ul class="simple-list">
    {% for membership_request in pending_requests %}
    <li>
        <span>{{ membership_request.user.username }}</span>
        <span>
            <form method="post" action="{% url 'checkin:membership_request_accept' festival_slug=request.festival.slug request_id=membership_request.id %}" style="display:inline">
                {% csrf_token %}
                <button type="submit">Accepter</button>
            </form>
            <form method="post" action="{% url 'checkin:membership_request_reject' festival_slug=request.festival.slug request_id=membership_request.id %}" style="display:inline">
                {% csrf_token %}
                <button type="submit">Refuser</button>
            </form>
        </span>
    </li>
    {% endfor %}
</ul>

<h2 class="panel-title">Bénévoles</h2>
<ul class="simple-list">
    {% for membership in memberships %}
    <li>
        <span>{{ membership.user.username }}</span>
        <form method="post" action="{% url 'checkin:volunteer_remove' festival_slug=request.festival.slug membership_id=membership.id %}" style="display:inline">
            {% csrf_token %}
            <button type="submit">Retirer l'accès</button>
        </form>
    </li>
    {% endfor %}
</ul>

<div class="form-section">
    <h2 class="panel-title">Créer un compte bénévole</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Créer</button>
    </form>
</div>
</div>
{% endblock %}
```

- [ ] **Step 4: Lancer la suite de tests complète**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: aucune régression — tous les tests vérifient du texte/des attributs `data-*`/`id`/URLs, jamais de classes CSS ni la structure exacte des balises englobantes ; l'ajout de `<div>`/`<span>` autour du contenu existant ne casse aucune assertion.

- [ ] **Step 5: Commit**

```bash
git add checkin/static/checkin/css/base.css checkin/templates/registration/login.html checkin/templates/checkin/signup.html checkin/templates/checkin/festival_create.html checkin/templates/checkin/select_festival.html checkin/templates/checkin/festival_search.html checkin/templates/checkin/edition_list.html checkin/templates/checkin/volunteer_list.html
git commit -m "feat: applique le nouveau systeme visuel aux pages secondaires"
```

---

### Task 5: Vérification manuelle complète (Playwright)

**Files:**
- Aucun fichier applicatif modifié — vérification uniquement.

**Interfaces:**
- Consumes: l'ensemble des tâches précédentes.
- Produces: rien — dernière étape du plan.

- [ ] **Step 1: Lancer la suite de tests complète**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: tous les tests passent, aucun `FAILED`.

- [ ] **Step 2: Vérification manuelle dans un navigateur (Playwright)**

Prérequis : lancer le serveur de développement en arrière-plan sur un port libre (ex. `manage.py runserver 127.0.0.1:8001 --noreload`), et disposer d'un compte organisateur avec un festival, une édition active, et quelques `Visit` sur plusieurs départements (créer ces données via `manage.py shell` si besoin, comme lors des vérifications précédentes).

Avec les outils `mcp__playwright__browser_navigate`, `browser_click`, `browser_snapshot`, `browser_take_screenshot`, `browser_console_messages` (charger leurs schémas via ToolSearch si besoin), dérouler :

1. Se connecter → vérifier le fond sombre par défaut sur la page d'enregistrement, le bouton ☀️ visible, l'absence d'erreur console.
2. Cliquer sur un groupe puis un département → vérifier la bannière de confirmation verte, les ombres/dégradés sur les boutons.
3. Cliquer sur ☀️ → vérifier le passage immédiat en thème clair (fond gris doux, boutons bleus). Recharger la page → le thème clair est conservé.
4. Aller sur la page statistiques (compte organisateur) → vérifier les cartes KPI, le classement en barres, les graphiques Chart.js et la carte de France, tous cohérents avec le thème clair actif.
5. Cliquer sur 🌙 → vérifier que la carte et les graphiques changent de couleur sans rechargement de page.
6. Parcourir les pages secondaires (`/inscription/`, `/login/`, `/festivals/`, `/festivals/creer/`, `/festivals/rejoindre/`, la page Éditions, la page Bénévoles) dans les deux thèmes → vérifier un rendu cohérent (cartes, listes, formulaires stylés), aucune couleur codée en dur visible (pas de zone blanche non stylée en thème sombre).
7. Vérifier la console du navigateur sur chaque page : aucune erreur JS (hors 404 favicon, déjà connu et sans impact).

- [ ] **Step 3: Nettoyage et vérification finale**

Nettoyer les données de test créées pour la vérification (via `manage.py shell`), arrêter le serveur, relancer `.venv/Scripts/python.exe -m pytest -v` une dernière fois pour confirmer l'absence de régression.

---
