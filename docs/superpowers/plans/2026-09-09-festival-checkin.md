# Application d'enregistrement des visiteurs par département — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire une application web Django permettant d'enregistrer en un ou deux clics le département/pays d'origine des visiteurs d'un festival photo, et de consulter des statistiques (carte, classement, évolution temporelle) — avec un support natif de plusieurs festivals indépendants (multi-tenant).

**Architecture:** Projet Django `festivalcount` avec une seule app `checkin`. Vues fonctionnelles classiques rendant des templates Django + JavaScript vanilla (fetch) pour l'interactivité. Isolation des données par festival via un modèle `Membership` (user × festival × rôle) vérifié par un décorateur de permission sur chaque vue. SQLite comme base de données.

**Tech Stack:** Django 6.1.1, Python 3.14, pytest + pytest-django, Chart.js (vendored localement), SVG statique pour la carte de France, JavaScript vanilla (aucun framework front).

## Global Constraints

- Django version : 6.1.1 exactement (spec : Stack technique).
- Python version : 3.14 (spec : Stack technique).
- Base de données : SQLite (spec : Stack technique).
- Aucune dépendance JS chargée depuis un CDN — tout fichier JS (Chart.js compris) est vendored dans `checkin/static/checkin/js/` (spec : Stack technique, pour un fonctionnement sans accès internet garanti).
- Pas de framework JS (React/Vue/HTMX) — JavaScript vanilla uniquement (spec : Stack technique).
- Tests avec `pytest` + `pytest-django`, pas `unittest.TestCase` (spec : Tests).
- Toutes les URLs applicatives (hors login/logout/admin) sont scopées par festival : `/f/<festival_slug>/…` (spec : Rôles et permissions).
- Isolation stricte entre festivals : un `Membership` sur le festival A ne donne aucun accès aux données du festival B (spec : Rôles et permissions).
- Une édition n'accepte des enregistrements que si `date_debut ≤ aujourd'hui ≤ date_fin` (spec : modèle `Edition`).

---

### Task 1: Bootstrap du projet Django + pytest-django

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `manage.py` (généré par `django-admin startproject`)
- Create: `festivalcount/__init__.py`, `festivalcount/settings.py`, `festivalcount/urls.py`, `festivalcount/asgi.py`, `festivalcount/wsgi.py`
- Create: `checkin/__init__.py`, `checkin/apps.py`, `checkin/models.py`, `checkin/admin.py`, `checkin/urls.py`, `checkin/views.py`
- Create: `checkin/tests/__init__.py`, `checkin/tests/test_bootstrap.py`
- Create: `templates/registration/login.html`
- Create: `checkin/templates/checkin/base.html`

**Interfaces:**
- Produces: réglages Django prêts à l'emploi ; noms d'URL `checkin:login`, `checkin:logout` ; template de base `checkin/base.html` avec un bloc `{% block content %}` que toutes les pages suivantes utiliseront.

- [ ] **Step 1: Créer `requirements.txt`**

```
Django==6.1.1
pytest
pytest-django
```

- [ ] **Step 2: Installer les dépendances**

Run: `pip install -r requirements.txt`
Expected: installation réussie de Django 6.1.1, pytest, pytest-django.

- [ ] **Step 3: Générer le projet Django**

Run: `django-admin startproject festivalcount .`
Expected: crée `manage.py` et le dossier `festivalcount/` avec `settings.py`, `urls.py`, `asgi.py`, `wsgi.py`, `__init__.py`.

- [ ] **Step 4: Générer l'app `checkin`**

Run: `python manage.py startapp checkin`
Expected: crée le dossier `checkin/` avec `models.py`, `admin.py`, `apps.py`, `views.py`, `tests.py`, `migrations/`.

- [ ] **Step 5: Remplacer `checkin/tests.py` par un package de tests**

Run: `rm checkin/tests.py && mkdir checkin/tests`

Create `checkin/tests/__init__.py` (fichier vide).

- [ ] **Step 6: Écrire `festivalcount/settings.py`**

```python
"""Django settings for festivalcount project."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-secret-key-change-me-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "checkin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "festivalcount.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "festivalcount.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "checkin" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "checkin:login"
LOGIN_REDIRECT_URL = "checkin:select_festival"
LOGOUT_REDIRECT_URL = "checkin:login"
```

- [ ] **Step 7: Écrire `festivalcount/urls.py`**

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("checkin.urls")),
]
```

- [ ] **Step 8: Écrire `checkin/urls.py`**

```python
from django.contrib.auth import views as auth_views
from django.urls import path

app_name = "checkin"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

- [ ] **Step 9: Créer `checkin/templates/checkin/base.html`**

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 10: Créer `checkin/static/checkin/css/base.css` (minimal pour l'instant)**

```css
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: system-ui, -apple-system, sans-serif;
    background-color: #f5f5f5;
    color: #1a1a1a;
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
    background-color: #fdecea;
    color: #611a15;
}

.message--success {
    background-color: #e6f4ea;
    color: #1e4620;
}
```

- [ ] **Step 11: Créer `templates/registration/login.html`**

```html
{% extends "checkin/base.html" %}
{% block title %}Connexion — Festival Count{% endblock %}
{% block content %}
<h1>Connexion</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Se connecter</button>
</form>
{% endblock %}
```

- [ ] **Step 12: Créer `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = festivalcount.settings
python_files = test_*.py
```

- [ ] **Step 13: Écrire le test de bootstrap `checkin/tests/test_bootstrap.py`**

```python
import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_can_create_and_authenticate_user():
    user = User.objects.create_user(username="testuser", password="pass12345")
    assert user.pk is not None
    assert user.check_password("pass12345") is True
```

- [ ] **Step 14: Lancer les tests**

Run: `pytest -v`
Expected: `1 passed`

- [ ] **Step 15: Vérifier la configuration Django**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 16: Commit**

```bash
git add requirements.txt pytest.ini manage.py festivalcount checkin templates .gitignore 2>/dev/null
git add -A
git commit -m "chore: bootstrap projet Django + pytest-django"
```

Note : créer d'abord un `.gitignore` avec au minimum :
```
__pycache__/
*.pyc
db.sqlite3
staticfiles/
.venv/
venv/
```

---

### Task 2: Modèle `Festival` + admin

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Create: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: rien (premier modèle).
- Produces: `checkin.models.Festival` avec champs `nom` (str), `slug` (str, unique) et `__str__() -> str` retournant `nom`.

- [ ] **Step 1: Écrire le test qui échoue**

`checkin/tests/test_models.py` :

```python
import pytest

from checkin.models import Festival


@pytest.mark.django_db
def test_festival_str_returns_nom():
    festival = Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    assert str(festival) == "Festival Photo de Tignecourt"


@pytest.mark.django_db
def test_festival_slug_is_unique():
    Festival.objects.create(nom="Festival A", slug="meme-slug")
    with pytest.raises(Exception):
        Festival.objects.create(nom="Festival B", slug="meme-slug")
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Festival' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

`checkin/models.py` :

```python
from django.db import models


class Festival(models.Model):
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0001_initial.py` avec le modèle `Festival`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `2 passed`

- [ ] **Step 6: Enregistrer dans l'admin**

`checkin/admin.py` :

```python
from django.contrib import admin

from checkin.models import Festival


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ["nom", "slug"]
    prepopulated_fields = {"slug": ["nom"]}
```

- [ ] **Step 7: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele Festival"
```

---

### Task 3: Modèle `Edition` + propriété `est_active`

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Modify: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`.
- Produces: `checkin.models.Edition` avec champs `festival` (FK Festival), `nom` (str), `date_debut` (date), `date_fin` (date), propriété `est_active` (bool), `__str__() -> str`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_models.py` :

```python
import datetime

from checkin.models import Edition


@pytest.mark.django_db
def test_edition_est_active_true_when_today_within_dates():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2026",
        date_debut=today - datetime.timedelta(days=1),
        date_fin=today + datetime.timedelta(days=1),
    )
    assert edition.est_active is True


@pytest.mark.django_db
def test_edition_est_active_false_when_dates_are_in_the_past():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2025",
        date_debut=today - datetime.timedelta(days=10),
        date_fin=today - datetime.timedelta(days=8),
    )
    assert edition.est_active is False


@pytest.mark.django_db
def test_edition_est_active_false_when_dates_are_in_the_future():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2027",
        date_debut=today + datetime.timedelta(days=8),
        date_fin=today + datetime.timedelta(days=10),
    )
    assert edition.est_active is False
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Edition' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

Ajouter à `checkin/models.py` :

```python
from django.utils import timezone


class Edition(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name="editions")
    nom = models.CharField(max_length=200)
    date_debut = models.DateField()
    date_fin = models.DateField()

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self):
        return f"{self.festival.nom} — {self.nom}"

    @property
    def est_active(self):
        today = timezone.localdate()
        return self.date_debut <= today <= self.date_fin
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0002_edition.py`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `5 passed`

- [ ] **Step 6: Enregistrer dans l'admin**

Ajouter à `checkin/admin.py` :

```python
from checkin.models import Edition


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["nom", "festival", "date_debut", "date_fin", "est_active"]
    list_filter = ["festival"]
```

- [ ] **Step 7: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele Edition avec propriete est_active"
```

---

### Task 4: Modèle `Membership`

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Modify: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`, `django.contrib.auth.models.User`.
- Produces: `checkin.models.Membership` avec champs `user` (FK User), `festival` (FK Festival), `role` (str parmi `Membership.ROLE_ORGANISATEUR = "organisateur"` et `Membership.ROLE_BENEVOLE = "benevole"`), contrainte d'unicité `(user, festival)`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_models.py` :

```python
from django.contrib.auth.models import User
from django.db import IntegrityError

from checkin.models import Membership


@pytest.mark.django_db
def test_membership_str_includes_role_label():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    membership = Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    assert "alice" in str(membership)
    assert "Festival A" in str(membership)


@pytest.mark.django_db
def test_membership_is_unique_per_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Membership' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

Ajouter à `checkin/models.py` :

```python
from django.conf import settings


class Membership(models.Model):
    ROLE_ORGANISATEUR = "organisateur"
    ROLE_BENEVOLE = "benevole"
    ROLE_CHOICES = [
        (ROLE_ORGANISATEUR, "Organisateur"),
        (ROLE_BENEVOLE, "Bénévole"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "festival"], name="unique_membership_per_user_festival"),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.festival.nom} ({self.get_role_display()})"
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0003_membership.py`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `7 passed`

- [ ] **Step 6: Enregistrer dans l'admin**

Ajouter à `checkin/admin.py` :

```python
from checkin.models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "festival", "role"]
    list_filter = ["festival", "role"]
```

- [ ] **Step 7: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele Membership (role par festival)"
```

---

### Task 5: Modèle `Origin`

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Modify: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: rien.
- Produces: `checkin.models.Origin` avec champs `code` (str, unique), `nom` (str), `type` (str parmi `Origin.TYPE_DEPARTEMENT`, `Origin.TYPE_DOM_TOM`, `Origin.TYPE_PAYS`, `Origin.TYPE_AUTRE`), `groupe` (str), `ordre_affichage` (int).

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_models.py` :

```python
from checkin.models import Origin


@pytest.mark.django_db
def test_origin_str_includes_code_and_nom():
    origin = Origin.objects.create(
        code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1
    )
    assert "75" in str(origin)
    assert "Paris" in str(origin)


@pytest.mark.django_db
def test_origin_code_is_unique():
    Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    with pytest.raises(Exception):
        Origin.objects.create(code="75", nom="Doublon", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=2)
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Origin' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

Ajouter à `checkin/models.py` :

```python
class Origin(models.Model):
    TYPE_DEPARTEMENT = "departement"
    TYPE_DOM_TOM = "dom_tom"
    TYPE_PAYS = "pays"
    TYPE_AUTRE = "autre"
    TYPE_CHOICES = [
        (TYPE_DEPARTEMENT, "Département"),
        (TYPE_DOM_TOM, "DOM-TOM"),
        (TYPE_PAYS, "Pays"),
        (TYPE_AUTRE, "Autre"),
    ]

    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    groupe = models.CharField(max_length=50)
    ordre_affichage = models.IntegerField()

    class Meta:
        ordering = ["ordre_affichage"]

    def __str__(self):
        return f"{self.code} — {self.nom}"
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0004_origin.py`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `9 passed`

- [ ] **Step 6: Enregistrer dans l'admin**

Ajouter à `checkin/admin.py` :

```python
from checkin.models import Origin


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "type", "groupe", "ordre_affichage"]
    list_filter = ["type", "groupe"]
```

- [ ] **Step 7: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele Origin (referentiel departements/pays)"
```

---

### Task 6: Données de référence des origines + migration de peuplement

**Files:**
- Create: `checkin/reference_data.py`
- Create: `checkin/migrations/0005_populate_origins.py`
- Create: `checkin/tests/test_reference_data.py`

**Interfaces:**
- Consumes: `checkin.models.Origin`.
- Produces: `checkin.reference_data.ORIGINS` — liste de 112 dicts `{"code", "nom", "type", "groupe", "ordre_affichage"}`, utilisée par la migration pour peupler la table `Origin`. Constantes de groupe : `GROUPE_01_19`, `GROUPE_2A_39`, `GROUPE_40_59`, `GROUPE_60_79`, `GROUPE_80_95`, `GROUPE_DOM_TOM`, `GROUPE_ETRANGER`.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_reference_data.py` :

```python
import pytest

from checkin.models import Origin
from checkin.reference_data import ORIGINS, GROUPE_DOM_TOM, GROUPE_ETRANGER


def test_origins_reference_data_has_112_entries():
    assert len(ORIGINS) == 112


def test_origins_reference_data_codes_are_unique():
    codes = [entry["code"] for entry in ORIGINS]
    assert len(codes) == len(set(codes))


def test_origins_reference_data_includes_autre_pays():
    autre = [entry for entry in ORIGINS if entry["code"] == "AUTRE"]
    assert len(autre) == 1
    assert autre[0]["type"] == Origin.TYPE_AUTRE
    assert autre[0]["groupe"] == GROUPE_ETRANGER


@pytest.mark.django_db
def test_migration_populates_112_origins():
    assert Origin.objects.count() == 112


@pytest.mark.django_db
def test_migration_populates_101_departements_et_dom_tom():
    count = Origin.objects.filter(type__in=[Origin.TYPE_DEPARTEMENT, Origin.TYPE_DOM_TOM]).count()
    assert count == 101


@pytest.mark.django_db
def test_migration_populates_dom_tom_group_with_5_entries():
    assert Origin.objects.filter(groupe=GROUPE_DOM_TOM).count() == 5
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_reference_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'checkin.reference_data'`

- [ ] **Step 3: Créer `checkin/reference_data.py`**

```python
"""Données de référence des origines (départements, DOM-TOM, pays), partagées entre tous les festivals."""
from checkin.models import Origin

GROUPE_01_19 = "01–19"
GROUPE_2A_39 = "2A/2B, 21–39"
GROUPE_40_59 = "40–59"
GROUPE_60_79 = "60–79"
GROUPE_80_95 = "80–95"
GROUPE_DOM_TOM = "DOM-TOM"
GROUPE_ETRANGER = "Étranger"

# (code, nom, type, groupe)
_ORIGINS_DATA = [
    ("01", "Ain", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("02", "Aisne", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("03", "Allier", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("04", "Alpes-de-Haute-Provence", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("05", "Hautes-Alpes", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("06", "Alpes-Maritimes", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("07", "Ardèche", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("08", "Ardennes", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("09", "Ariège", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("10", "Aube", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("11", "Aude", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("12", "Aveyron", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("13", "Bouches-du-Rhône", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("14", "Calvados", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("15", "Cantal", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("16", "Charente", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("17", "Charente-Maritime", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("18", "Cher", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("19", "Corrèze", Origin.TYPE_DEPARTEMENT, GROUPE_01_19),
    ("2A", "Corse-du-Sud", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("2B", "Haute-Corse", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("21", "Côte-d'Or", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("22", "Côtes-d'Armor", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("23", "Creuse", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("24", "Dordogne", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("25", "Doubs", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("26", "Drôme", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("27", "Eure", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("28", "Eure-et-Loir", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("29", "Finistère", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("30", "Gard", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("31", "Haute-Garonne", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("32", "Gers", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("33", "Gironde", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("34", "Hérault", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("35", "Ille-et-Vilaine", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("36", "Indre", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("37", "Indre-et-Loire", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("38", "Isère", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("39", "Jura", Origin.TYPE_DEPARTEMENT, GROUPE_2A_39),
    ("40", "Landes", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("41", "Loir-et-Cher", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("42", "Loire", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("43", "Haute-Loire", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("44", "Loire-Atlantique", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("45", "Loiret", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("46", "Lot", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("47", "Lot-et-Garonne", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("48", "Lozère", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("49", "Maine-et-Loire", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("50", "Manche", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("51", "Marne", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("52", "Haute-Marne", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("53", "Mayenne", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("54", "Meurthe-et-Moselle", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("55", "Meuse", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("56", "Morbihan", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("57", "Moselle", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("58", "Nièvre", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("59", "Nord", Origin.TYPE_DEPARTEMENT, GROUPE_40_59),
    ("60", "Oise", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("61", "Orne", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("62", "Pas-de-Calais", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("63", "Puy-de-Dôme", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("64", "Pyrénées-Atlantiques", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("65", "Hautes-Pyrénées", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("66", "Pyrénées-Orientales", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("67", "Bas-Rhin", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("68", "Haut-Rhin", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("69", "Rhône", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("70", "Haute-Saône", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("71", "Saône-et-Loire", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("72", "Sarthe", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("73", "Savoie", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("74", "Haute-Savoie", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("75", "Paris", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("76", "Seine-Maritime", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("77", "Seine-et-Marne", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("78", "Yvelines", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("79", "Deux-Sèvres", Origin.TYPE_DEPARTEMENT, GROUPE_60_79),
    ("80", "Somme", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("81", "Tarn", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("82", "Tarn-et-Garonne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("83", "Var", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("84", "Vaucluse", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("85", "Vendée", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("86", "Vienne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("87", "Haute-Vienne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("88", "Vosges", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("89", "Yonne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("90", "Territoire de Belfort", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("91", "Essonne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("92", "Hauts-de-Seine", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("93", "Seine-Saint-Denis", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("94", "Val-de-Marne", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("95", "Val-d'Oise", Origin.TYPE_DEPARTEMENT, GROUPE_80_95),
    ("971", "Guadeloupe", Origin.TYPE_DOM_TOM, GROUPE_DOM_TOM),
    ("972", "Martinique", Origin.TYPE_DOM_TOM, GROUPE_DOM_TOM),
    ("973", "Guyane", Origin.TYPE_DOM_TOM, GROUPE_DOM_TOM),
    ("974", "La Réunion", Origin.TYPE_DOM_TOM, GROUPE_DOM_TOM),
    ("976", "Mayotte", Origin.TYPE_DOM_TOM, GROUPE_DOM_TOM),
    ("BE", "Belgique", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("CH", "Suisse", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("DE", "Allemagne", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("IT", "Italie", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("ES", "Espagne", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("LU", "Luxembourg", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("NL", "Pays-Bas", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("GB", "Royaume-Uni", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("PT", "Portugal", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("MC", "Monaco", Origin.TYPE_PAYS, GROUPE_ETRANGER),
    ("AUTRE", "Autre pays", Origin.TYPE_AUTRE, GROUPE_ETRANGER),
]

ORIGINS = [
    {"code": code, "nom": nom, "type": type_, "groupe": groupe, "ordre_affichage": index}
    for index, (code, nom, type_, groupe) in enumerate(_ORIGINS_DATA, start=1)
]
```

- [ ] **Step 4: Générer une migration vide**

Run: `python manage.py makemigrations checkin --empty --name populate_origins`
Expected: crée `checkin/migrations/0005_populate_origins.py` avec une dépendance automatiquement fixée sur `0004_origin`.

- [ ] **Step 5: Compléter la migration générée**

Éditer `checkin/migrations/0005_populate_origins.py` pour ajouter les fonctions et l'opération (garder la liste `dependencies` telle que générée à l'étape précédente) :

```python
from django.db import migrations

from checkin.reference_data import ORIGINS


def populate_origins(apps, schema_editor):
    Origin = apps.get_model("checkin", "Origin")
    Origin.objects.bulk_create([Origin(**data) for data in ORIGINS])


def remove_origins(apps, schema_editor):
    Origin = apps.get_model("checkin", "Origin")
    Origin.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0004_origin"),
    ]

    operations = [
        migrations.RunPython(populate_origins, remove_origins),
    ]
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_reference_data.py -v`
Expected: `6 passed` (pytest-django applique toutes les migrations, y compris celle-ci, à la base de test)

- [ ] **Step 7: Appliquer la migration à la base de développement**

Run: `python manage.py migrate`
Expected: `Applying checkin.0005_populate_origins... OK`

- [ ] **Step 8: Commit**

```bash
git add checkin/reference_data.py checkin/migrations checkin/tests/test_reference_data.py
git commit -m "feat: peuple le referentiel Origin (101 departements + DOM-TOM + pays)"
```

---

### Task 7: Modèle `Visit`

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Modify: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: `checkin.models.Edition`, `checkin.models.Origin`, `django.contrib.auth.models.User`.
- Produces: `checkin.models.Visit` avec champs `edition` (FK Edition), `origin` (FK Origin), `precision_libre` (str, optionnel), `horodatage` (datetime, auto), `enregistre_par` (FK User).

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_models.py` :

```python
from checkin.models import Visit


@pytest.mark.django_db
def test_visit_records_horodatage_automatically():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    edition = Edition.objects.create(
        festival=festival, nom="Édition 2026",
        date_debut=datetime.date.today(), date_fin=datetime.date.today(),
    )
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = User.objects.create_user(username="alice", password="pass12345")

    visit = Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)

    assert visit.horodatage is not None


@pytest.mark.django_db
def test_visit_precision_libre_is_optional():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    edition = Edition.objects.create(
        festival=festival, nom="Édition 2026",
        date_debut=datetime.date.today(), date_fin=datetime.date.today(),
    )
    origin = Origin.objects.create(code="AUTRE", nom="Autre pays", type=Origin.TYPE_AUTRE, groupe="Étranger", ordre_affichage=1)
    user = User.objects.create_user(username="alice", password="pass12345")

    visit = Visit.objects.create(edition=edition, origin=origin, enregistre_par=user, precision_libre="Canada")

    assert visit.precision_libre == "Canada"
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Visit' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

Ajouter à `checkin/models.py` :

```python
class Visit(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name="visits")
    origin = models.ForeignKey(Origin, on_delete=models.PROTECT, related_name="visits")
    precision_libre = models.CharField(max_length=100, blank=True, default="")
    horodatage = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="visits")

    class Meta:
        ordering = ["-horodatage"]

    def __str__(self):
        return f"{self.origin.nom} — {self.horodatage:%d/%m/%Y %H:%M}"
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0006_visit.py`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `11 passed`

- [ ] **Step 6: Enregistrer dans l'admin**

Ajouter à `checkin/admin.py` :

```python
from checkin.models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ["origin", "edition", "horodatage", "enregistre_par"]
    list_filter = ["edition__festival", "edition", "origin__type"]
```

- [ ] **Step 7: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele Visit"
```

---

### Task 8: Vue de sélection du festival (`select_festival`)

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/select_festival.html`
- Create: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: `checkin.models.Membership`.
- Produces: URL nommée `checkin:select_festival` (chemin `festivals/`), vue `select_festival` listant les `Membership` de l'utilisateur connecté.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views.py` :

```python
import pytest
from django.urls import reverse

from checkin.models import Festival, Membership


@pytest.mark.django_db
def test_select_festival_requires_login(client):
    response = client.get(reverse("checkin:select_festival"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_select_festival_lists_user_memberships(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    festival = Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 200
    assert "Festival Photo de Tignecourt" in response.content.decode()


@pytest.mark.django_db
def test_select_festival_shows_message_when_no_memberships(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert "aucun festival" in response.content.decode()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:select_festival` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from checkin.models import Membership


@login_required
def select_festival(request):
    memberships = Membership.objects.filter(user=request.user).select_related("festival")
    return render(request, "checkin/select_festival.html", {"memberships": memberships})
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` (ajouter l'import et l'entrée) :

```python
from checkin import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
]
```

- [ ] **Step 5: Créer le template**

`checkin/templates/checkin/select_festival.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Mes festivals — Festival Count{% endblock %}
{% block content %}
<h1>Mes festivals</h1>
{% if memberships %}
<ul class="festival-list">
    {% for membership in memberships %}
    <li>{{ membership.festival.nom }} — {{ membership.get_role_display }}</li>
    {% endfor %}
</ul>
{% else %}
<p>Vous n'avez accès à aucun festival pour le moment. Contactez l'organisateur de votre festival.</p>
{% endif %}
{% endblock %}
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/select_festival.html checkin/tests/test_views.py
git commit -m "feat: ajoute la vue de selection du festival apres connexion"
```

---

### Task 9: Décorateur de permission `membership_required`

**Files:**
- Create: `checkin/permissions.py`
- Create: `checkin/tests/test_permissions.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`, `checkin.models.Membership`, URL nommée `checkin:select_festival` (Task 8).
- Produces: `checkin.permissions.membership_required(roles=None)` — décorateur pour vues fonctionnelles prenant `festival_slug` en premier argument positionnel après `request`. Attache `request.festival` (Festival) et `request.membership` (Membership) sur succès. Redirige vers `checkin:select_festival` avec un message d'erreur si accès refusé (pas de membership, ou rôle non autorisé). Exige une authentification préalable (redirige vers la page de login sinon).

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_permissions.py` :

```python
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from checkin.models import Festival, Membership
from checkin.permissions import membership_required


def _prepare_request(request):
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)
    return request


@membership_required()
def _any_role_view(request, festival_slug):
    return HttpResponse("ok")


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def _organisateur_only_view(request, festival_slug):
    return HttpResponse("ok")


@pytest.mark.django_db
def test_membership_required_allows_access_for_any_role():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 200
    assert request.festival == festival
    assert request.membership.role == Membership.ROLE_BENEVOLE


@pytest.mark.django_db
def test_membership_required_redirects_when_no_membership():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 302
    assert response.url == "/festivals/"


@pytest.mark.django_db
def test_membership_required_redirects_when_role_not_allowed():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _organisateur_only_view(request, festival_slug=festival.slug)

    assert response.status_code == 302


@pytest.mark.django_db
def test_membership_required_redirects_anonymous_user_to_login():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = AnonymousUser()

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 302
    assert "/login/" in response.url
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_permissions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'checkin.permissions'`

- [ ] **Step 3: Implémenter le décorateur**

`checkin/permissions.py` :

```python
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from checkin.models import Festival, Membership


def membership_required(roles=None):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, festival_slug, *args, **kwargs):
            festival = get_object_or_404(Festival, slug=festival_slug)
            membership = Membership.objects.filter(user=request.user, festival=festival).first()
            if membership is None or (roles is not None and membership.role not in roles):
                messages.error(request, "Vous n'avez pas accès à cette page.")
                return redirect("checkin:select_festival")
            request.festival = festival
            request.membership = membership
            return view_func(request, festival_slug, *args, **kwargs)
        return wrapped_view
    return decorator
```

- [ ] **Step 4: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_permissions.py -v`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add checkin/permissions.py checkin/tests/test_permissions.py
git commit -m "feat: ajoute le decorateur membership_required"
```

---

### Task 10: Sélecteur d'édition active

**Files:**
- Create: `checkin/selectors.py`
- Create: `checkin/tests/test_selectors.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`, `checkin.models.Edition`.
- Produces: `checkin.selectors.get_active_edition(festival) -> Edition | None`.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_selectors.py` :

```python
import datetime

import pytest

from checkin.models import Edition, Festival
from checkin.selectors import get_active_edition


@pytest.mark.django_db
def test_get_active_edition_returns_edition_within_dates():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)

    assert get_active_edition(festival) == edition


@pytest.mark.django_db
def test_get_active_edition_returns_none_when_no_active_edition():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(
        festival=festival, nom="2025",
        date_debut=today - datetime.timedelta(days=10),
        date_fin=today - datetime.timedelta(days=8),
    )

    assert get_active_edition(festival) is None


@pytest.mark.django_db
def test_get_active_edition_ignores_other_festivals():
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    today = datetime.date.today()
    Edition.objects.create(festival=festival_b, nom="2026", date_debut=today, date_fin=today)

    assert get_active_edition(festival_a) is None
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_selectors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'checkin.selectors'`

- [ ] **Step 3: Implémenter le sélecteur**

`checkin/selectors.py` :

```python
from django.utils import timezone


def get_active_edition(festival):
    today = timezone.localdate()
    return festival.editions.filter(date_debut__lte=today, date_fin__gte=today).first()
```

- [ ] **Step 4: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_selectors.py -v`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add checkin/selectors.py checkin/tests/test_selectors.py
git commit -m "feat: ajoute le selecteur d'edition active"
```

---

### Task 11: Vue d'enregistrement — GET (structure de la page)

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/register.html`
- Modify: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.selectors.get_active_edition`, `checkin.models.Origin`.
- Produces: URL nommée `checkin:register` (chemin `f/<slug:festival_slug>/enregistrement/`), template `checkin/register.html` avec les sections `#screen-groups` et `#screen-origins`, et un data island JSON `#origins-data` consommé par le JavaScript des tâches suivantes.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views.py` :

```python
import datetime

from checkin.models import Edition, Origin


@pytest.mark.django_db
def test_register_shows_no_active_edition_message(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert "Aucune édition en cours" in response.content.decode()


@pytest.mark.django_db
def test_register_shows_origins_when_edition_is_active(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert "Paris" in response.content.decode()


@pytest.mark.django_db
def test_register_denies_access_without_membership(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:register` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
from checkin.models import Origin
from checkin.permissions import membership_required
from checkin.selectors import get_active_edition


@membership_required()
def register(request, festival_slug):
    edition = get_active_edition(request.festival)
    origins = Origin.objects.all() if edition else Origin.objects.none()
    return render(
        request,
        "checkin/register.html",
        {"edition": edition, "origins": origins},
    )
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` :

```python
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
]
```

- [ ] **Step 5: Créer le template**

`checkin/templates/checkin/register.html` :

```html
{% extends "checkin/base.html" %}
{% load static %}
{% block title %}Enregistrement — {{ request.festival.nom }}{% endblock %}
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

<section id="screen-groups" data-edition-id="{{ edition.id }}">
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
{% endif %}
{% endblock %}
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v`
Expected: `6 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/register.html checkin/tests/test_views.py
git commit -m "feat: ajoute la structure de la page d'enregistrement"
```

---

### Task 12: API POST créer un `Visit`

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Modify: `checkin/templates/checkin/register.html`
- Create: `checkin/tests/test_views_visit_api.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.selectors.get_active_edition`, `checkin.models.Origin`, `checkin.models.Visit`.
- Produces: URL nommée `checkin:visit_create` (chemin `f/<slug:festival_slug>/enregistrement/visites/`), acceptant un POST JSON `{"origin_code": str, "precision_libre": str (optionnel)}`, renvoyant `{"id": int, "origin_nom": str}` avec le statut 201.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_visit_api.py` :

```python
import datetime
import json

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin, Visit


@pytest.mark.django_db
def test_visit_create_records_a_visit(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
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
    assert data["origin_nom"] == "Paris"
    visit = Visit.objects.get(id=data["id"])
    assert visit.edition == edition
    assert visit.origin == origin
    assert visit.enregistre_par == user


@pytest.mark.django_db
def test_visit_create_stores_precision_libre_for_autre(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    Origin.objects.create(code="AUTRE", nom="Autre pays", type=Origin.TYPE_AUTRE, groupe="Étranger", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_create", kwargs={"festival_slug": festival.slug}),
        data=json.dumps({"origin_code": "AUTRE", "precision_libre": "Canada"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    visit = Visit.objects.get(id=response.json()["id"])
    assert visit.precision_libre == "Canada"


@pytest.mark.django_db
def test_visit_create_rejects_when_no_active_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_create", kwargs={"festival_slug": festival.slug}),
        data=json.dumps({"origin_code": "75"}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert Visit.objects.count() == 0
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_visit_api.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:visit_create` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from checkin.models import Visit


@require_POST
@membership_required()
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

    precision_libre = payload.get("precision_libre") or ""

    visit = Visit.objects.create(
        edition=edition,
        origin=origin,
        enregistre_par=request.user,
        precision_libre=precision_libre,
    )

    return JsonResponse({"id": visit.id, "origin_nom": origin.nom}, status=201)
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` :

```python
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
    path("f/<slug:festival_slug>/enregistrement/visites/", views.visit_create, name="visit_create"),
]
```

- [ ] **Step 5: Exposer l'URL au template pour le JavaScript**

Modifier `checkin/templates/checkin/register.html`, la balise `<section id="screen-groups" ...>` :

```html
<section id="screen-groups" data-edition-id="{{ edition.id }}" data-create-url="{% url 'checkin:visit_create' festival_slug=request.festival.slug %}">
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_visit_api.py -v`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/register.html checkin/tests/test_views_visit_api.py
git commit -m "feat: ajoute l'API de creation d'un Visit"
```

---

### Task 13: API POST annuler un `Visit`

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Modify: `checkin/templates/checkin/register.html`
- Modify: `checkin/tests/test_views_visit_api.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.models.Visit`.
- Produces: URL nommée `checkin:visit_cancel` (chemin `f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/`), POST supprimant le `Visit` s'il appartient bien au festival ciblé, sinon 404.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views_visit_api.py` :

```python
@pytest.mark.django_db
def test_visit_cancel_deletes_the_visit(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    visit = Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_cancel", kwargs={"festival_slug": festival.slug, "visit_id": visit.id})
    )

    assert response.status_code == 200
    assert not Visit.objects.filter(id=visit.id).exists()


@pytest.mark.django_db
def test_visit_cancel_returns_404_for_visit_of_another_festival(client, django_user_model):
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    today = datetime.date.today()
    edition_b = Edition.objects.create(festival=festival_b, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user_b = django_user_model.objects.create_user(username="bob", password="pass12345")
    Membership.objects.create(user=user_b, festival=festival_b, role=Membership.ROLE_BENEVOLE)
    visit = Visit.objects.create(edition=edition_b, origin=origin, enregistre_par=user_b)

    user_a = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user_a, festival=festival_a, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:visit_cancel", kwargs={"festival_slug": festival_a.slug, "visit_id": visit.id})
    )

    assert response.status_code == 404
    assert Visit.objects.filter(id=visit.id).exists()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_visit_api.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:visit_cancel` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
@require_POST
@membership_required()
def visit_cancel(request, festival_slug, visit_id):
    visit = Visit.objects.filter(id=visit_id, edition__festival=request.festival).first()
    if visit is None:
        return JsonResponse({"error": "Visite introuvable."}, status=404)
    visit.delete()
    return JsonResponse({"deleted": True})
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` :

```python
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
    path("f/<slug:festival_slug>/enregistrement/visites/", views.visit_create, name="visit_create"),
    path("f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/", views.visit_cancel, name="visit_cancel"),
]
```

- [ ] **Step 5: Exposer l'URL au template pour le JavaScript**

Modifier `checkin/templates/checkin/register.html`, la balise `<section id="screen-groups" ...>` (ajouter l'attribut, en gardant `data-create-url`) :

```html
<section id="screen-groups" data-edition-id="{{ edition.id }}" data-create-url="{% url 'checkin:visit_create' festival_slug=request.festival.slug %}" data-cancel-url-base="{% url 'checkin:visit_cancel' festival_slug=request.festival.slug visit_id=0 %}">
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_visit_api.py -v`
Expected: `5 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/register.html checkin/tests/test_views_visit_api.py
git commit -m "feat: ajoute l'API d'annulation d'un Visit"
```

---

### Task 14: CSS mobile-first de la page d'enregistrement

**Files:**
- Modify: `checkin/static/checkin/css/base.css`

**Interfaces:**
- Consumes: la structure HTML de `checkin/templates/checkin/register.html` (Task 11) — classes `.button-grid`, `.group-button`, `.origin-button`, `.confirmation`, `.error-message`, `.no-active-edition`.
- Produces: styles visuels ; aucune interface de code consommée par d'autres tâches.

- [ ] **Step 1: Ajouter les styles à `checkin/static/checkin/css/base.css`**

```css
.no-active-edition {
    text-align: center;
    font-size: 1.5rem;
    padding: 3rem 1rem;
    color: #555;
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
    font-weight: 600;
    border: none;
    border-radius: 12px;
    background-color: #2563eb;
    color: #ffffff;
    cursor: pointer;
    padding: 0.5rem;
    touch-action: manipulation;
}

.group-button:active,
.origin-button:active {
    background-color: #1d4ed8;
}

.group-button:disabled,
.origin-button:disabled {
    background-color: #93a3c4;
    cursor: not-allowed;
}

#back-button {
    min-height: 56px;
    font-size: 1.1rem;
    margin: 1rem;
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 8px;
    background-color: #e5e7eb;
    cursor: pointer;
}

.confirmation {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background-color: #1e4620;
    color: #ffffff;
    padding: 1rem;
    font-size: 1.1rem;
}

.confirmation button {
    min-height: 48px;
    padding: 0.5rem 1.25rem;
    border: none;
    border-radius: 8px;
    background-color: #ffffff;
    color: #1e4620;
    font-weight: 600;
    cursor: pointer;
}

.error-message {
    background-color: #611a15;
    color: #ffffff;
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
    border: 1px solid #ccc;
    border-radius: 8px;
}

#autre-form button {
    min-height: 48px;
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 8px;
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    cursor: pointer;
}

@media (min-width: 768px) {
    .button-grid {
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    }
}
```

- [ ] **Step 2: Vérifier visuellement**

Run: `python manage.py runserver`, se connecter avec un compte bénévole de test, ouvrir `/f/<slug>/enregistrement/` sur un navigateur redimensionné en largeur mobile (375px) et en largeur tablette (768px).
Expected : boutons larges et lisibles, pas de débordement horizontal.

- [ ] **Step 3: Commit**

```bash
git add checkin/static/checkin/css/base.css
git commit -m "style: ajoute le CSS mobile-first de la page d'enregistrement"
```

---

### Task 15: JavaScript vanilla de la page d'enregistrement

**Files:**
- Create: `checkin/static/checkin/js/register.js`
- Modify: `checkin/templates/checkin/register.html`

**Interfaces:**
- Consumes: le data island JSON `#origins-data`, les attributs `data-create-url` et `data-cancel-url-base` sur `#screen-groups` (Tasks 11-13).
- Produces: comportement interactif complet de la page d'enregistrement. Aucune fonction exportée consommée par d'autres fichiers (script autonome).

- [ ] **Step 1: Créer `checkin/static/checkin/js/register.js`**

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
```

- [ ] **Step 2: Charger le script dans le template**

Modifier `checkin/templates/checkin/register.html`, juste avant `{% endif %}` final, après le `<script id="origins-data" ...>` :

```html
<script src="{% static 'checkin/js/register.js' %}" defer></script>
```

- [ ] **Step 3: Vérification manuelle end-to-end**

Run: `python manage.py runserver`

Avec un compte bénévole connecté sur `/f/<slug>/enregistrement/` (édition active requise) :
1. Cliquer un groupe → vérifier l'affichage de l'écran 2 avec les bons départements/pays.
2. Cliquer un département → vérifier le message de confirmation et le retour à l'écran 1.
3. Cliquer « Annuler » dans les 5 secondes → vérifier via l'admin Django (`/admin/checkin/visit/`) que le `Visit` a bien été supprimé.
4. Cliquer « Étranger » puis « Autre » → saisir un pays → valider → vérifier la confirmation.
5. Couper le réseau (mode avion / DevTools offline) puis cliquer un département → vérifier l'affichage du message d'erreur.
6. Double-cliquer rapidement sur un département → vérifier qu'un seul `Visit` est créé (boutons désactivés ~1s).

Expected : les 6 comportements ci-dessus fonctionnent comme décrit.

- [ ] **Step 4: Commit**

```bash
git add checkin/static/checkin/js/register.js checkin/templates/checkin/register.html
git commit -m "feat: ajoute l'interactivite JS de la page d'enregistrement"
```

---

### Task 16: Service de calcul des statistiques

**Files:**
- Create: `checkin/stats.py`
- Create: `checkin/tests/test_stats.py`

**Interfaces:**
- Consumes: `checkin.models.Visit`, `checkin.models.Edition`.
- Produces: `checkin.stats.get_key_figures(edition) -> dict` (clés `total_visiteurs`, `nombre_departements`, `nombre_pays`) ; `checkin.stats.get_ranking(edition) -> list[dict]` (clés `origin__code`, `origin__nom`, `nombre`, triée décroissant) ; `checkin.stats.get_hourly_evolution(edition) -> list[dict]` (clés `heure` (str ISO), `nombre`, triée croissant).

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_stats.py` :

```python
import datetime

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from checkin.models import Edition, Festival, Origin, Visit
from checkin.stats import get_hourly_evolution, get_key_figures, get_ranking


@pytest.mark.django_db
def test_get_key_figures_counts_total_and_distinct_origins():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    rhone = Origin.objects.create(code="69", nom="Rhône", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=2)
    belgique = Origin.objects.create(code="BE", nom="Belgique", type=Origin.TYPE_PAYS, groupe="Étranger", ordre_affichage=3)

    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=belgique, enregistre_par=user)

    figures = get_key_figures(edition)

    assert figures["total_visiteurs"] == 4
    assert figures["nombre_departements"] == 2
    assert figures["nombre_pays"] == 1


@pytest.mark.django_db
def test_get_key_figures_ignores_other_editions():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition_a = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    edition_b = Edition.objects.create(
        festival=festival, nom="2025",
        date_debut=today - datetime.timedelta(days=365),
        date_fin=today - datetime.timedelta(days=364),
    )
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    Visit.objects.create(edition=edition_b, origin=paris, enregistre_par=user)

    figures = get_key_figures(edition_a)

    assert figures["total_visiteurs"] == 0


@pytest.mark.django_db
def test_get_ranking_orders_by_visit_count_descending():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    rhone = Origin.objects.create(code="69", nom="Rhône", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=2)

    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)

    ranking = get_ranking(edition)

    assert ranking[0]["origin__code"] == "75"
    assert ranking[0]["nombre"] == 2
    assert ranking[1]["origin__code"] == "69"
    assert ranking[1]["nombre"] == 1


@pytest.mark.django_db
def test_get_hourly_evolution_groups_visits_by_hour():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)

    visit1 = Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    visit2 = Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.filter(id=visit1.id).update(horodatage=timezone.make_aware(datetime.datetime(2026, 6, 20, 10, 15)))
    Visit.objects.filter(id=visit2.id).update(horodatage=timezone.make_aware(datetime.datetime(2026, 6, 20, 10, 45)))

    evolution = get_hourly_evolution(edition)

    assert len(evolution) == 1
    assert evolution[0]["nombre"] == 2
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_stats.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'checkin.stats'`

- [ ] **Step 3: Implémenter le service**

`checkin/stats.py` :

```python
from django.db.models import Count
from django.db.models.functions import TruncHour

from checkin.models import Origin, Visit


def get_key_figures(edition):
    visits = Visit.objects.filter(edition=edition)
    total = visits.count()
    nombre_departements = (
        visits.filter(origin__type__in=[Origin.TYPE_DEPARTEMENT, Origin.TYPE_DOM_TOM])
        .values("origin")
        .distinct()
        .count()
    )
    nombre_pays = (
        visits.filter(origin__type__in=[Origin.TYPE_PAYS, Origin.TYPE_AUTRE])
        .values("origin")
        .distinct()
        .count()
    )
    return {
        "total_visiteurs": total,
        "nombre_departements": nombre_departements,
        "nombre_pays": nombre_pays,
    }


def get_ranking(edition):
    return list(
        Visit.objects.filter(edition=edition)
        .values("origin__code", "origin__nom")
        .annotate(nombre=Count("id"))
        .order_by("-nombre")
    )


def get_hourly_evolution(edition):
    rows = (
        Visit.objects.filter(edition=edition)
        .annotate(heure=TruncHour("horodatage"))
        .values("heure")
        .annotate(nombre=Count("id"))
        .order_by("heure")
    )
    return [{"heure": row["heure"].isoformat(), "nombre": row["nombre"]} for row in rows]
```

- [ ] **Step 4: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_stats.py -v`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add checkin/stats.py checkin/tests/test_stats.py
git commit -m "feat: ajoute le service de calcul des statistiques"
```

---

### Task 17: Vue de statistiques — GET (structure de la page)

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/stats.html`
- Create: `checkin/tests/test_views_stats.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.selectors.get_active_edition`, `checkin.stats.get_key_figures/get_ranking/get_hourly_evolution`.
- Produces: URL nommée `checkin:stats` (chemin `f/<slug:festival_slug>/stats/`), accessible uniquement aux `Membership.ROLE_ORGANISATEUR`. Accepte un paramètre GET `edition` (id) pour choisir l'édition consultée ; par défaut, l'édition active, sinon la plus récente.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_stats.py` :

```python
import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin, Visit


@pytest.mark.django_db
def test_stats_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_stats_shows_key_figures_for_selected_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Paris" in content
    assert 'data-total="1"' in content


@pytest.mark.django_db
def test_stats_allows_selecting_a_past_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    edition_past = Edition.objects.create(
        festival=festival, nom="Édition 2025",
        date_debut=today - datetime.timedelta(days=365),
        date_fin=today - datetime.timedelta(days=364),
    )
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(
        reverse("checkin:stats", kwargs={"festival_slug": festival.slug}),
        {"edition": edition_past.id},
    )

    assert response.status_code == 200
    assert f'value="{edition_past.id}" selected' in response.content.decode()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_stats.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:stats` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
from checkin.models import Membership
from checkin.stats import get_hourly_evolution, get_key_figures, get_ranking


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
        context["ranking"] = get_ranking(edition)
        context["hourly_evolution"] = get_hourly_evolution(edition)
        context["is_current_edition"] = edition == active_edition

    return render(request, "checkin/stats.html", context)
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` :

```python
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
    path("f/<slug:festival_slug>/enregistrement/visites/", views.visit_create, name="visit_create"),
    path("f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/", views.visit_cancel, name="visit_cancel"),
    path("f/<slug:festival_slug>/stats/", views.stats, name="stats"),
]
```

- [ ] **Step 5: Créer le template**

`checkin/templates/checkin/stats.html` :

```html
{% extends "checkin/base.html" %}
{% load static %}
{% block title %}Statistiques — {{ request.festival.nom }}{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }} — Statistiques</h1>

{% if not editions %}
<p>Aucune édition pour ce festival.</p>
{% else %}
<form method="get" id="edition-selector-form">
    <label for="edition-selector">Édition :</label>
    <select name="edition" id="edition-selector" onchange="this.form.submit()">
        {% for e in editions %}
        <option value="{{ e.id }}" {% if selected_edition and e.id == selected_edition.id %}selected{% endif %}>{{ e.nom }}</option>
        {% endfor %}
    </select>
</form>

{% if selected_edition %}
<section id="key-figures"
         data-total="{{ key_figures.total_visiteurs }}"
         data-departements="{{ key_figures.nombre_departements }}"
         data-pays="{{ key_figures.nombre_pays }}">
    <p>Total visiteurs : <strong id="total-visiteurs">{{ key_figures.total_visiteurs }}</strong></p>
    <p>Départements représentés : <strong id="total-departements">{{ key_figures.nombre_departements }}</strong></p>
    <p>Pays représentés : <strong id="total-pays">{{ key_figures.nombre_pays }}</strong></p>
</section>

<table id="ranking-table">
    <thead><tr><th>Origine</th><th>Visiteurs</th></tr></thead>
    <tbody>
        {% for row in ranking %}
        <tr><td>{{ row.origin__code }} — {{ row.origin__nom }}</td><td>{{ row.nombre }}</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}
{% endif %}
{% endblock %}
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_stats.py -v`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/stats.html checkin/tests/test_views_stats.py
git commit -m "feat: ajoute la structure de la page de statistiques"
```

---

### Task 18: API JSON des statistiques (auto-refresh)

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Modify: `checkin/templates/checkin/stats.html`
- Create: `checkin/tests/test_views_stats_api.py`

**Interfaces:**
- Consumes: `checkin.stats.get_key_figures/get_ranking/get_hourly_evolution`.
- Produces: URL nommée `checkin:stats_data` (chemin `f/<slug:festival_slug>/stats/data/`), GET avec paramètre `edition` (id), renvoie `{"key_figures": {...}, "ranking": [...], "hourly_evolution": [...]}`.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_stats_api.py` :

```python
import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin, Visit


@pytest.mark.django_db
def test_stats_data_returns_json_for_organisateur(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.create(code="75", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.get(
        reverse("checkin:stats_data", kwargs={"festival_slug": festival.slug}),
        {"edition": edition.id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["key_figures"]["total_visiteurs"] == 1
    assert data["ranking"][0]["origin__code"] == "75"


@pytest.mark.django_db
def test_stats_data_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(
        reverse("checkin:stats_data", kwargs={"festival_slug": festival.slug}),
        {"edition": edition.id},
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_stats_data_returns_404_for_edition_of_another_festival(client, django_user_model):
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    today = datetime.date.today()
    edition_b = Edition.objects.create(festival=festival_b, nom="Édition 2026", date_debut=today, date_fin=today)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival_a, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(
        reverse("checkin:stats_data", kwargs={"festival_slug": festival_a.slug}),
        {"edition": edition_b.id},
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_stats_api.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:stats_data` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def stats_data(request, festival_slug):
    edition_id = request.GET.get("edition")
    edition = request.festival.editions.filter(id=edition_id).first()
    if edition is None:
        return JsonResponse({"error": "Édition introuvable."}, status=404)

    return JsonResponse({
        "key_figures": get_key_figures(edition),
        "ranking": get_ranking(edition),
        "hourly_evolution": get_hourly_evolution(edition),
    })
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py` (ajouter avant la dernière entrée) :

```python
    path("f/<slug:festival_slug>/stats/", views.stats, name="stats"),
    path("f/<slug:festival_slug>/stats/data/", views.stats_data, name="stats_data"),
```

- [ ] **Step 5: Exposer l'URL au template**

Modifier `checkin/templates/checkin/stats.html`, la balise `<section id="key-figures" ...>` (ajouter les attributs, garder les existants) :

```html
<section id="key-figures"
         data-total="{{ key_figures.total_visiteurs }}"
         data-departements="{{ key_figures.nombre_departements }}"
         data-pays="{{ key_figures.nombre_pays }}"
         data-stats-data-url="{% url 'checkin:stats_data' festival_slug=request.festival.slug %}"
         data-edition-id="{{ selected_edition.id }}"
         data-is-current="{{ is_current_edition|yesno:'true,false' }}">
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_stats_api.py -v`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/stats.html checkin/tests/test_views_stats_api.py
git commit -m "feat: ajoute l'API JSON des statistiques pour l'auto-refresh"
```

---

### Task 19: Intégration de Chart.js (classement + évolution temporelle)

**Files:**
- Create: `checkin/static/checkin/js/vendor/chart.umd.min.js` (vendored)
- Create: `checkin/static/checkin/js/stats.js`
- Modify: `checkin/templates/checkin/stats.html`

**Interfaces:**
- Consumes: les data islands JSON `ranking-data`/`evolution-data`, les attributs `data-stats-data-url`/`data-edition-id`/`data-is-current` sur `#key-figures` (Task 18).
- Produces: `window.updateMapColors(ranking)` — hook optionnel appelé après chaque rafraîchissement, consommé par la carte SVG (Task 20).

- [ ] **Step 1: Télécharger Chart.js (build UMD vendored, pas de CDN au runtime)**

Run:
```bash
mkdir -p checkin/static/checkin/js/vendor
curl -sL -o checkin/static/checkin/js/vendor/chart.umd.min.js "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"
wc -c checkin/static/checkin/js/vendor/chart.umd.min.js
```
Expected: le fichier fait plusieurs centaines de Ko (pas une page d'erreur HTML). Si l'URL n'est plus disponible, télécharger la dernière version 4.x stable de `chart.js` (build UMD, fichier `dist/chart.umd.min.js`) depuis le registre npm et l'enregistrer au même emplacement.

- [ ] **Step 2: Ajouter les canvases et les données au template**

Modifier `checkin/templates/checkin/stats.html`, juste après la balise `</table>` fermant `#ranking-table`, avant le `{% endif %}` qui ferme `{% if selected_edition %}` :

```html
<canvas id="ranking-chart" height="300"></canvas>
<canvas id="evolution-chart" height="300"></canvas>
<div id="map-container"></div>

{{ ranking|json_script:"ranking-data" }}
{{ hourly_evolution|json_script:"evolution-data" }}

<script src="{% static 'checkin/js/vendor/chart.umd.min.js' %}"></script>
<script src="{% static 'checkin/js/stats.js' %}" defer></script>
```

- [ ] **Step 3: Créer `checkin/static/checkin/js/stats.js`**

```javascript
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
```

- [ ] **Step 4: Vérification manuelle**

Run: `python manage.py runserver`, se connecter en tant qu'organisateur d'un festival ayant des `Visit` enregistrées, ouvrir `/f/<slug>/stats/`.
Expected : le graphique en barres (classement) et le graphique en ligne (évolution horaire) s'affichent avec les bonnes valeurs, sans erreur dans la console du navigateur.

- [ ] **Step 5: Commit**

```bash
git add checkin/static/checkin/js/vendor/chart.umd.min.js checkin/static/checkin/js/stats.js checkin/templates/checkin/stats.html
git commit -m "feat: integre Chart.js pour le classement et l'evolution temporelle"
```

---

### Task 20: Carte de France chloroplèthe

**Files:**
- Create: `checkin/static/checkin/svg/france-departements.svg` (asset externe, licence libre)
- Create: `checkin/static/checkin/js/map.js`
- Modify: `checkin/templates/checkin/stats.html`

**Interfaces:**
- Consumes: `ranking-data` (data island JSON, Task 19), `#map-container` (Task 19).
- Produces: `window.updateMapColors(ranking)`, appelée par `stats.js` (Task 19) à chaque rafraîchissement.

- [ ] **Step 1: Sourcer un SVG des départements français**

Rechercher un fichier SVG « carte vierge des départements français » sous licence libre (domaine public, CC0 ou CC-BY — vérifier la licence avant utilisation), avec un tracé (`<path>`) distinct par département. L'enregistrer sous `checkin/static/checkin/svg/france-departements.svg`.

Ouvrir le fichier et identifier comment chaque `<path>` est identifié (attribut `id`, `data-code`, ou `class`) et le format des codes utilisé (ex. `"01"`, `"FR-01"`, ou le nom complet du département). Noter ce format : il sera nécessaire à l'étape 3.

- [ ] **Step 2: Exposer l'URL du SVG et le conteneur**

Modifier `checkin/templates/checkin/stats.html`, remplacer `<div id="map-container"></div>` (ajouté Task 19) par :

```html
<div id="map-container" data-svg-url="{% static 'checkin/svg/france-departements.svg' %}"></div>
```

Ajouter le script de la carte juste avant `<script src="{% static 'checkin/js/stats.js' %}" defer></script>` :

```html
<script src="{% static 'checkin/js/map.js' %}" defer></script>
```

- [ ] **Step 3: Créer `checkin/static/checkin/js/map.js`**

```javascript
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
```

- [ ] **Step 4: Adapter `findDepartmentPath()` si nécessaire**

Si, à l'étape 5, la console affiche l'avertissement « aucun tracé trouvé » pour la plupart des codes, ouvrir le fichier SVG et ajouter dans `findDepartmentPath()` le motif exact observé à l'étape 1 (par exemple un attribut `class` contenant le code, ou un nom de département en toutes lettres à faire correspondre via une table de correspondance code → nom à ajouter en tête de `map.js`).

Note : les DOM-TOM et les pays étrangers ne figurent pas sur cette carte (elle ne couvre que la France métropolitaine) ; leurs effectifs restent visibles via les chiffres clés et le tableau de classement.

- [ ] **Step 5: Vérification manuelle**

Run: `python manage.py runserver`, ouvrir `/f/<slug>/stats/` pour une édition ayant des `Visit` sur plusieurs départements métropolitains.
Expected : la carte s'affiche avec les départements concernés colorés selon leur affluence relative ; aucun avertissement « aucun tracé trouvé » dans la console.

- [ ] **Step 6: Commit**

```bash
git add checkin/static/checkin/svg/france-departements.svg checkin/static/checkin/js/map.js checkin/templates/checkin/stats.html
git commit -m "feat: ajoute la carte de France chloroplethe"
```

---

### Task 21: Auto-redirection de `select_festival` vers l'enregistrement/les stats

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/templates/checkin/select_festival.html`
- Modify: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: URLs `checkin:register` (Task 11) et `checkin:stats` (Task 17), `checkin.models.Membership`.
- Produces: `select_festival` redirige automatiquement quand l'utilisateur n'a qu'un seul `Membership` (vers `checkin:register` pour un bénévole, `checkin:stats` pour un organisateur) ; affiche des liens réels vers ces pages quand il y en a plusieurs.

- [ ] **Step 1: Mettre à jour le test existant à un seul membership**

Dans `checkin/tests/test_views.py`, remplacer le test `test_select_festival_lists_user_memberships` (il échouerait désormais : un seul membership déclenche une redirection) par :

```python
@pytest.mark.django_db
def test_select_festival_lists_user_memberships_when_several(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    festival_a = Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    Membership.objects.create(user=user, festival=festival_a, role=Membership.ROLE_BENEVOLE)
    Membership.objects.create(user=user, festival=festival_b, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 200
    assert "Festival Photo de Tignecourt" in response.content.decode()
```

- [ ] **Step 2: Écrire les nouveaux tests qui échouent**

Ajouter à `checkin/tests/test_views.py` :

```python
@pytest.mark.django_db
def test_select_festival_redirects_when_single_membership_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 302
    assert response.url == reverse("checkin:register", kwargs={"festival_slug": festival.slug})


@pytest.mark.django_db
def test_select_festival_redirects_when_single_membership_organisateur(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 302
    assert response.url == reverse("checkin:stats", kwargs={"festival_slug": festival.slug})


@pytest.mark.django_db
def test_select_festival_lists_links_when_multiple_memberships(client, django_user_model):
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival_a, role=Membership.ROLE_BENEVOLE)
    Membership.objects.create(user=user, festival=festival_b, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 200
    content = response.content.decode()
    assert reverse("checkin:register", kwargs={"festival_slug": festival_a.slug}) in content
    assert reverse("checkin:stats", kwargs={"festival_slug": festival_b.slug}) in content
```

- [ ] **Step 3: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v`
Expected: les 3 nouveaux tests échouent (pas encore de redirection ni de liens réels).

- [ ] **Step 4: Mettre à jour la vue**

Ajouter `redirect` à l'import existant de `django.shortcuts` en tête de `checkin/views.py` (jusqu'ici seul `render` y était importé) :

```python
from django.shortcuts import redirect, render
```

Remplacer ensuite la fonction `select_festival` par :

```python
@login_required
def select_festival(request):
    memberships = Membership.objects.filter(user=request.user).select_related("festival")
    if memberships.count() == 1:
        membership = memberships.first()
        target_view = "checkin:stats" if membership.role == Membership.ROLE_ORGANISATEUR else "checkin:register"
        return redirect(target_view, festival_slug=membership.festival.slug)
    return render(request, "checkin/select_festival.html", {"memberships": memberships})
```

- [ ] **Step 5: Mettre à jour le template**

Remplacer dans `checkin/templates/checkin/select_festival.html` :

```html
<ul class="festival-list">
    {% for membership in memberships %}
    <li>
        <a href="{% if membership.role == 'organisateur' %}{% url 'checkin:stats' festival_slug=membership.festival.slug %}{% else %}{% url 'checkin:register' festival_slug=membership.festival.slug %}{% endif %}">
            {{ membership.festival.nom }} — {{ membership.get_role_display }}
        </a>
    </li>
    {% endfor %}
</ul>
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v`
Expected: tous les tests passent.

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/templates/checkin/select_festival.html checkin/tests/test_views.py
git commit -m "feat: auto-redirige select_festival vers l'enregistrement ou les stats"
```

---

### Task 22: Gestion des éditions (liste + création)

**Files:**
- Create: `checkin/forms.py`
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/edition_list.html`
- Create: `checkin/tests/test_views_editions.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.models.Edition`.
- Produces: `checkin.forms.EditionForm` (ModelForm sur `Edition`, champs `nom`, `date_debut`, `date_fin`, rejette `date_fin < date_debut`). URL nommée `checkin:edition_list` (chemin `f/<slug:festival_slug>/editions/`), réservée aux organisateurs.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_editions.py` :

```python
import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership


@pytest.mark.django_db
def test_edition_list_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_edition_list_shows_existing_editions(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert "Édition 2026" in response.content.decode()


@pytest.mark.django_db
def test_edition_list_creates_a_new_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}),
        {"nom": "Édition 2027", "date_debut": "2027-06-19", "date_fin": "2027-06-21"},
    )

    assert response.status_code == 302
    edition = Edition.objects.get(nom="Édition 2027")
    assert edition.festival == festival


@pytest.mark.django_db
def test_edition_list_rejects_end_date_before_start_date(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}),
        {"nom": "Édition invalide", "date_debut": "2027-06-21", "date_fin": "2027-06-19"},
    )

    assert response.status_code == 200
    assert not Edition.objects.filter(nom="Édition invalide").exists()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_editions.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:edition_list` n'existe pas encore)

- [ ] **Step 3: Créer le formulaire**

`checkin/forms.py` :

```python
from django import forms

from checkin.models import Edition


class EditionForm(forms.ModelForm):
    class Meta:
        model = Edition
        fields = ["nom", "date_debut", "date_fin"]
        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}),
            "date_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
        if date_debut and date_fin and date_fin < date_debut:
            raise forms.ValidationError("La date de fin doit être postérieure ou égale à la date de début.")
        return cleaned_data
```

- [ ] **Step 4: Implémenter la vue**

Ajouter à `checkin/views.py` :

```python
from checkin.forms import EditionForm


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def edition_list(request, festival_slug):
    editions = request.festival.editions.all()

    if request.method == "POST":
        form = EditionForm(request.POST)
        if form.is_valid():
            edition = form.save(commit=False)
            edition.festival = request.festival
            edition.save()
            messages.success(request, "Édition créée avec succès.")
            return redirect("checkin:edition_list", festival_slug=festival_slug)
    else:
        form = EditionForm()

    return render(request, "checkin/edition_list.html", {"editions": editions, "form": form})
```

Ajouter également l'import du module `messages` en tête de `checkin/views.py` si ce n'est pas déjà fait :

```python
from django.contrib import messages
```

- [ ] **Step 5: Ajouter l'URL**

Modifier `checkin/urls.py` (ajouter avant la dernière entrée) :

```python
    path("f/<slug:festival_slug>/editions/", views.edition_list, name="edition_list"),
```

- [ ] **Step 6: Créer le template**

`checkin/templates/checkin/edition_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Éditions — {{ request.festival.nom }}{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }} — Éditions</h1>

<ul>
    {% for edition in editions %}
    <li>{{ edition.nom }} ({{ edition.date_debut }} – {{ edition.date_fin }}){% if edition.est_active %} — en cours{% endif %}</li>
    {% endfor %}
</ul>

<h2>Créer une nouvelle édition</h2>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Créer</button>
</form>
{% endblock %}
```

- [ ] **Step 7: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_editions.py -v`
Expected: `4 passed`

- [ ] **Step 8: Commit**

```bash
git add checkin/forms.py checkin/views.py checkin/urls.py checkin/templates/checkin/edition_list.html checkin/tests/test_views_editions.py
git commit -m "feat: ajoute la gestion des editions par les organisateurs"
```

---

### Task 23: Gestion des bénévoles

**Files:**
- Modify: `checkin/forms.py`
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/volunteer_list.html`
- Create: `checkin/tests/test_views_volunteers.py`

**Interfaces:**
- Consumes: `checkin.permissions.membership_required`, `checkin.models.Membership`, `django.contrib.auth.models.User`.
- Produces: `checkin.forms.VolunteerCreationForm` (champs `username`, `password`, rejette un nom d'utilisateur déjà pris). URLs nommées `checkin:volunteer_list` (chemin `f/<slug:festival_slug>/benevoles/`) et `checkin:volunteer_remove` (chemin `f/<slug:festival_slug>/benevoles/<int:membership_id>/retirer/`), réservées aux organisateurs.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_volunteers.py` :

```python
import pytest
from django.urls import reverse

from checkin.models import Festival, Membership


@pytest.mark.django_db
def test_volunteer_list_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_volunteer_list_creates_a_volunteer_account(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}),
        {"username": "bob", "password": "pass67890"},
    )

    assert response.status_code == 302
    new_membership = Membership.objects.get(user__username="bob", festival=festival)
    assert new_membership.role == Membership.ROLE_BENEVOLE
    assert new_membership.user.check_password("pass67890")


@pytest.mark.django_db
def test_volunteer_list_rejects_duplicate_username(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    django_user_model.objects.create_user(username="bob", password="pass12345")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}),
        {"username": "bob", "password": "pass67890"},
    )

    assert response.status_code == 200
    assert Membership.objects.filter(festival=festival, user__username="bob").count() == 0


@pytest.mark.django_db
def test_volunteer_remove_deletes_membership(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    volunteer_user = django_user_model.objects.create_user(username="bob", password="pass12345")
    volunteer_membership = Membership.objects.create(user=volunteer_user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_remove", kwargs={"festival_slug": festival.slug, "membership_id": volunteer_membership.id})
    )

    assert response.status_code == 302
    assert not Membership.objects.filter(id=volunteer_membership.id).exists()
    assert django_user_model.objects.filter(username="bob").exists()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_volunteers.py -v`
Expected: FAIL — `NoReverseMatch` (les URLs `checkin:volunteer_list`/`checkin:volunteer_remove` n'existent pas encore)

- [ ] **Step 3: Ajouter le formulaire**

Ajouter à `checkin/forms.py` :

```python
from django.contrib.auth.models import User


class VolunteerCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username
```

- [ ] **Step 4: Implémenter les vues**

Ajouter à `checkin/views.py` :

```python
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from checkin.forms import VolunteerCreationForm


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def volunteer_list(request, festival_slug):
    memberships = Membership.objects.filter(
        festival=request.festival, role=Membership.ROLE_BENEVOLE
    ).select_related("user")

    if request.method == "POST":
        form = VolunteerCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            Membership.objects.create(user=user, festival=request.festival, role=Membership.ROLE_BENEVOLE)
            messages.success(request, "Compte bénévole créé avec succès.")
            return redirect("checkin:volunteer_list", festival_slug=festival_slug)
    else:
        form = VolunteerCreationForm()

    return render(request, "checkin/volunteer_list.html", {"memberships": memberships, "form": form})


@require_POST
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def volunteer_remove(request, festival_slug, membership_id):
    membership = Membership.objects.filter(
        id=membership_id, festival=request.festival, role=Membership.ROLE_BENEVOLE
    ).first()
    if membership is not None:
        membership.delete()
        messages.success(request, "Accès du bénévole retiré.")
    return redirect("checkin:volunteer_list", festival_slug=festival_slug)
```

- [ ] **Step 5: Ajouter les URLs**

Modifier `checkin/urls.py` (ajouter à la fin) :

```python
    path("f/<slug:festival_slug>/benevoles/", views.volunteer_list, name="volunteer_list"),
    path("f/<slug:festival_slug>/benevoles/<int:membership_id>/retirer/", views.volunteer_remove, name="volunteer_remove"),
```

- [ ] **Step 6: Créer le template**

`checkin/templates/checkin/volunteer_list.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Bénévoles — {{ request.festival.nom }}{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }} — Bénévoles</h1>

<ul>
    {% for membership in memberships %}
    <li>
        {{ membership.user.username }}
        <form method="post" action="{% url 'checkin:volunteer_remove' festival_slug=request.festival.slug membership_id=membership.id %}" style="display:inline">
            {% csrf_token %}
            <button type="submit">Retirer l'accès</button>
        </form>
    </li>
    {% endfor %}
</ul>

<h2>Créer un compte bénévole</h2>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Créer</button>
</form>
{% endblock %}
```

- [ ] **Step 7: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_volunteers.py -v`
Expected: `4 passed`

- [ ] **Step 8: Commit**

```bash
git add checkin/forms.py checkin/views.py checkin/urls.py checkin/templates/checkin/volunteer_list.html checkin/tests/test_views_volunteers.py
git commit -m "feat: ajoute la gestion des benevoles par les organisateurs"
```

---

### Task 24: README + vérification finale end-to-end

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: l'ensemble du projet.
- Produces: documentation de lancement ; aucune interface de code.

- [ ] **Step 1: Écrire `README.md`**

```markdown
# Festival Count

Application Django d'enregistrement du département/pays d'origine des visiteurs d'un festival photo, avec statistiques et graphiques. Supporte plusieurs festivals indépendants (multi-tenant).

## Prérequis

- Python 3.14
- pip

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Création d'un festival (première fois)

1. Lancer `python manage.py runserver` et se connecter sur `/admin/` avec le compte superuser.
2. Créer un `Festival` (nom + slug).
3. Créer une `Edition` pour ce festival (nom + dates du week-end du festival).
4. Créer un compte `User` pour le premier organisateur (ou utiliser le compte superuser).
5. Créer un `Membership` liant ce compte au festival avec le rôle « Organisateur ».
6. Se déconnecter de `/admin/`, se connecter sur `/login/` avec ce compte : vous êtes redirigé vers les statistiques du festival. Depuis là, la page « Bénévoles » (accessible depuis `/f/<slug>/benevoles/`) permet de créer les comptes bénévoles sans repasser par l'admin.

## Lancer l'application

```bash
python manage.py runserver
```

## Lancer les tests

```bash
pytest -v
```
```

- [ ] **Step 2: Lancer la suite de tests complète**

Run: `pytest -v`
Expected: tous les tests passent, aucun `FAILED` dans la sortie.

- [ ] **Step 3: Vérification manuelle end-to-end**

Suivre les étapes du README pour créer un festival de test, une édition active (dates couvrant aujourd'hui), un compte organisateur et, depuis l'application, un compte bénévole. Puis :

1. Se connecter en tant que bénévole → enregistrer plusieurs visiteurs dans différents départements/groupes, y compris « Étranger » → « Autre ».
2. Se connecter en tant qu'organisateur → ouvrir la page statistiques → vérifier que les chiffres clés, le classement, le graphique d'évolution et la carte reflètent les visites enregistrées.
3. Créer une deuxième édition (dates passées) depuis la page « Éditions » → vérifier qu'elle apparaît dans le sélecteur de la page statistiques et que ses données sont vides.
4. Retirer l'accès du bénévole créé → vérifier qu'il ne peut plus se connecter à la page d'enregistrement (redirection avec message).

Expected : les 4 parcours ci-dessus fonctionnent sans erreur serveur (500) ni comportement inattendu.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: ajoute le README de lancement du projet"
```

---
