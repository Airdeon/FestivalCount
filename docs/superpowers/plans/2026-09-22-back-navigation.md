# Navigation de retour entre les pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un lien de retour fixe sur chaque page vers sa page parente logique, pour permettre une navigation prévisible entre les pages de l'application (aucune ne se lie actuellement à une autre).

**Architecture:** Un bloc Django `{% block back_link %}{% endblock %}` dans `checkin/templates/checkin/base.html`, surchargé par chaque template concerné avec un lien `<a class="nav-back">` statique server-rendered vers l'URL de sa page parente. Aucun JavaScript, aucune dépendance à l'historique du navigateur.

**Tech Stack:** Django templates, CSS (tokens existants du système de thème clair/sombre).

## Global Constraints

- Aucune nouvelle couleur codée en dur : `.nav-back` consomme uniquement les tokens CSS existants (`--color-surface`, `--color-text`, `--shadow-card`, `--radius-sm`, `--transition-theme`) définis dans `checkin/static/checkin/css/base.css`.
- Pas de JavaScript, pas de `history.back()` — uniquement des liens `<a href>` server-rendered via `{% url %}`.
- Le bloc `{% block back_link %}` dans `base.html` doit être en dehors du `{% if user.is_authenticated %}` qui protège le bouton de thème et le formulaire de déconnexion — le lien de retour doit s'afficher aussi sur les pages non authentifiées (`signup.html`).
- Hiérarchie exacte à respecter (voir spec `docs/superpowers/specs/2026-09-22-back-navigation-design.md`) : `login`/`select_festival` n'ont aucun lien de retour ; `signup` → `login` ; `festival_create`/`festival_search`/`register`/`stats` → `select_festival` ; `edition_list`/`volunteer_list` → `stats`.
- Aucune régression sur la suite de tests existante (89 tests avant cette tâche).

---

### Task 1: Bloc de retour dans base.html, style CSS, et application aux 7 pages

**Files:**
- Modify: `checkin/templates/checkin/base.html`
- Modify: `checkin/static/checkin/css/base.css`
- Modify: `checkin/templates/checkin/signup.html`
- Modify: `checkin/templates/checkin/festival_create.html`
- Modify: `checkin/templates/checkin/festival_search.html`
- Modify: `checkin/templates/checkin/register.html`
- Modify: `checkin/templates/checkin/stats.html`
- Modify: `checkin/templates/checkin/edition_list.html`
- Modify: `checkin/templates/checkin/volunteer_list.html`
- Test: `checkin/tests/test_views.py`
- Test: `checkin/tests/test_views_festivals.py`
- Test: `checkin/tests/test_views_stats.py`
- Test: `checkin/tests/test_views_editions.py`
- Test: `checkin/tests/test_views_volunteers.py`

**Interfaces:**
- Consumes: tokens CSS du système de thème (Task 1-4 du plan `2026-09-21-ui-redesign.md`, déjà fusionné sur `main`) : `--color-surface`, `--color-text`, `--shadow-card`, `--radius-sm`, `--transition-theme`.
- Produces: bloc de template `{% block back_link %}` (consommé uniquement par les templates listés ci-dessus) et classe CSS `.nav-back`.

- [ ] **Step 1: Ajouter le bloc `back_link` dans `base.html`**

Remplacer le contenu de `checkin/templates/checkin/base.html` :

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
    {% block back_link %}{% endblock %}
    <main>
        {% block content %}{% endblock %}
    </main>
    <script src="{% static 'checkin/js/theme.js' %}" defer></script>
</body>
</html>
```

(Seul changement : la ligne `{% block back_link %}{% endblock %}` ajoutée juste avant `<main>`.)

- [ ] **Step 2: Ajouter le style `.nav-back`**

Ajouter à la fin de `checkin/static/checkin/css/base.css` :

```css

.nav-back {
    position: fixed;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 10;
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: var(--radius-sm);
    background: var(--color-surface);
    color: var(--color-text);
    text-decoration: none;
    font-weight: 700;
    box-shadow: var(--shadow-card);
    transition: var(--transition-theme);
}
```

- [ ] **Step 3: `signup.html` → retour vers `login`**

Remplacer le contenu de `checkin/templates/checkin/signup.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un compte — Festival Count{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:login' %}" class="nav-back">← Connexion</a>
{% endblock %}
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

- [ ] **Step 4: `festival_create.html` → retour vers `select_festival`**

Remplacer le contenu de `checkin/templates/checkin/festival_create.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un festival — Festival Count{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:select_festival' %}" class="nav-back">← Mes festivals</a>
{% endblock %}
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

- [ ] **Step 5: `festival_search.html` → retour vers `select_festival`**

Remplacer le contenu de `checkin/templates/checkin/festival_search.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Rejoindre un festival — Festival Count{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:select_festival' %}" class="nav-back">← Mes festivals</a>
{% endblock %}
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

- [ ] **Step 6: `register.html` → retour vers `select_festival`**

Remplacer le contenu de `checkin/templates/checkin/register.html` :

```html
{% extends "checkin/base.html" %}
{% load static %}
{% block title %}Enregistrement — {{ request.festival.nom }}{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:select_festival' %}" class="nav-back">← Mes festivals</a>
{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }}</h1>

{% if not edition %}
<p class="no-active-edition">Aucune édition en cours actuellement.</p>
{% else %}
<div id="confirmation" class="confirmation" hidden>
    <span id="confirmation-text"></span>
    <button type="button" id="cancel-button">Annuler</button>
</div>
<div id="error-message" class="error-message" hidden></div>

<section id="screen-groups" data-edition-id="{{ edition.id }}" data-create-url="{% url 'checkin:visit_create' festival_slug=request.festival.slug %}" data-cancel-url-base="{% url 'checkin:visit_cancel' festival_slug=request.festival.slug visit_id=0 %}">
    <h2>Choisissez un groupe</h2>
    <div class="button-grid" id="group-buttons"></div>
</section>

<section id="screen-origins" hidden>
    <button type="button" id="back-button">← Retour</button>
    <h2 id="selected-group-title"></h2>
    <div class="button-grid" id="origin-buttons"></div>
    <div id="autre-form" hidden>
        <input type="text" id="autre-input" placeholder="Précisez le pays">
        <button type="button" id="autre-submit">Valider</button>
    </div>
</section>

<script id="origins-data" type="application/json">
[
    {% for origin in origins %}
    {"code": "{{ origin.code }}", "nom": "{{ origin.nom|escapejs }}", "groupe": "{{ origin.groupe|escapejs }}", "type": "{{ origin.type }}"}{% if not forloop.last %},{% endif %}
    {% endfor %}
]
</script>
<script src="{% static 'checkin/js/register.js' %}" defer></script>
{% endif %}
{% endblock %}
```

(Seul changement : le bloc `back_link` ajouté après `{% block title %}`. Le reste du fichier, y compris le bouton `#back-button` interne à l'écran de sélection d'origine, est inchangé — ce bouton gère une transition entre deux sections de la même page, sans rapport avec la navigation entre pages.)

- [ ] **Step 7: `stats.html` → retour vers `select_festival`**

Remplacer le contenu de `checkin/templates/checkin/stats.html` :

```html
{% extends "checkin/base.html" %}
{% load static %}
{% block title %}Statistiques — {{ request.festival.nom }}{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:select_festival' %}" class="nav-back">← Mes festivals</a>
{% endblock %}
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

(Seul changement : le bloc `back_link` ajouté après `{% block title %}`. Le reste du fichier est inchangé.)

- [ ] **Step 8: `edition_list.html` → retour vers `stats`**

Remplacer le contenu de `checkin/templates/checkin/edition_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Éditions — {{ request.festival.nom }}{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:stats' festival_slug=request.festival.slug %}" class="nav-back">← Statistiques</a>
{% endblock %}
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

- [ ] **Step 9: `volunteer_list.html` → retour vers `stats`**

Remplacer le contenu de `checkin/templates/checkin/volunteer_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Bénévoles — {{ request.festival.nom }}{% endblock %}
{% block back_link %}
<a href="{% url 'checkin:stats' festival_slug=request.festival.slug %}" class="nav-back">← Statistiques</a>
{% endblock %}
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

- [ ] **Step 10: Ajouter les tests**

Ajouter à `checkin/tests/test_views.py` (après `test_signup_redirects_authenticated_user`) :

```python
def test_signup_page_shows_back_link_to_login(client):
    response = client.get(reverse("checkin:signup"))
    assert response.status_code == 200
    assert reverse("checkin:login") in response.content.decode()


@pytest.mark.django_db
def test_register_shows_back_link_to_select_festival(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:select_festival") in response.content.decode()
```

Ajouter à `checkin/tests/test_views_festivals.py` (à la fin du fichier) :

```python
@pytest.mark.django_db
def test_festival_create_shows_back_link_to_select_festival(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:festival_create"))

    assert response.status_code == 200
    assert reverse("checkin:select_festival") in response.content.decode()


@pytest.mark.django_db
def test_festival_search_shows_back_link_to_select_festival(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:festival_search"))

    assert response.status_code == 200
    assert reverse("checkin:select_festival") in response.content.decode()
```

Ajouter à `checkin/tests/test_views_stats.py` (à la fin du fichier) :

```python
@pytest.mark.django_db
def test_stats_shows_back_link_to_select_festival(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:select_festival") in response.content.decode()
```

Ajouter à `checkin/tests/test_views_editions.py` (à la fin du fichier) :

```python
@pytest.mark.django_db
def test_edition_list_shows_back_link_to_stats(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:stats", kwargs={"festival_slug": festival.slug}) in response.content.decode()
```

Ajouter à `checkin/tests/test_views_volunteers.py` (à la fin du fichier) :

```python
@pytest.mark.django_db
def test_volunteer_list_shows_back_link_to_stats(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:stats", kwargs={"festival_slug": festival.slug}) in response.content.decode()
```

- [ ] **Step 11: Lancer la suite de tests complète**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: 96 tests passent (89 existants + 7 nouveaux), aucun `FAILED`.

- [ ] **Step 12: Commit**

```bash
git add checkin/templates/checkin/base.html checkin/static/checkin/css/base.css checkin/templates/checkin/signup.html checkin/templates/checkin/festival_create.html checkin/templates/checkin/festival_search.html checkin/templates/checkin/register.html checkin/templates/checkin/stats.html checkin/templates/checkin/edition_list.html checkin/templates/checkin/volunteer_list.html checkin/tests/test_views.py checkin/tests/test_views_festivals.py checkin/tests/test_views_stats.py checkin/tests/test_views_editions.py checkin/tests/test_views_volunteers.py
git commit -m "feat: ajoute des liens de retour entre les pages"
```

---
