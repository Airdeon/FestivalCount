# Inscription libre et self-service festival — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre à n'importe qui de créer un compte, puis soit créer son propre festival (devenant Organisateur), soit demander à rejoindre un festival existant en tant que Bénévole sous réserve de validation, et ajouter un bouton de déconnexion fonctionnel.

**Architecture:** Extension du projet Django `festivalcount` / app `checkin` existants. Réutilisation maximale des briques d'authentification Django (`LoginView`, `LogoutView`, `UserCreationForm`). Un nouveau modèle `MembershipRequest` matérialise les demandes d'adhésion en attente de validation par un Organisateur.

**Tech Stack:** Identique au projet existant — Django 6.1.1, Python 3.14, pytest + pytest-django, templates Django, JavaScript vanilla (aucun JS nouveau requis pour cette fonctionnalité, purement des formulaires POST classiques).

## Global Constraints

- Réutiliser `django.contrib.auth.views.LoginView`/`LogoutView` (déjà en place) et `django.contrib.auth.forms.UserCreationForm` pour l'inscription — ne pas réécrire de validation de mot de passe maison (spec : Inscription).
- `MembershipRequest` ne porte pas de champ `role` : une demande concerne toujours le rôle `Membership.ROLE_BENEVOLE` (spec : Modèle de données).
- Contrainte d'unicité `(user, festival)` sur `MembershipRequest`, et refus de créer une demande si un `Membership` existe déjà pour ce couple (spec : Modèle de données).
- Les actions Accepter/Refuser une demande sont réservées à `Membership.ROLE_ORGANISATEUR` du festival concerné, via le décorateur `membership_required` existant (spec : Traitement des demandes).
- La création directe d'un compte bénévole par l'organisateur (`VolunteerCreationForm`, vue `volunteer_list`) reste inchangée et cohabite avec les demandes (spec : Traitement des demandes).
- Tests avec `pytest` + `pytest-django`, cohérent avec le reste du projet.

---

### Task 1: Modèle `MembershipRequest` + admin

**Files:**
- Modify: `checkin/models.py`
- Modify: `checkin/admin.py`
- Modify: `checkin/tests/test_models.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`, `django.contrib.auth.models.User`.
- Produces: `checkin.models.MembershipRequest` avec champs `user` (FK User), `festival` (FK Festival), `created_at` (datetime, auto), contrainte d'unicité `(user, festival)`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_models.py` (le fichier importe déjà `pytest`, `User`, `IntegrityError`, `Festival` depuis les tâches précédentes) :

```python
from checkin.models import MembershipRequest


@pytest.mark.django_db
def test_membership_request_str_includes_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=user, festival=festival)
    assert "alice" in str(membership_request)
    assert "Festival A" in str(membership_request)


@pytest.mark.django_db
def test_membership_request_is_unique_per_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    MembershipRequest.objects.create(user=user, festival=festival)
    with pytest.raises(IntegrityError):
        MembershipRequest.objects.create(user=user, festival=festival)
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'MembershipRequest' from 'checkin.models'`

- [ ] **Step 3: Implémenter le modèle**

Ajouter à `checkin/models.py` :

```python
class MembershipRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership_requests")
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name="membership_requests")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "festival"], name="unique_membership_request_per_user_festival"),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.festival.nom}"
```

- [ ] **Step 4: Générer la migration**

Run: `python manage.py makemigrations checkin`
Expected: crée `checkin/migrations/0007_membershiprequest.py`.

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_models.py -v`
Expected: `13 passed` (11 tests précédents + 2 nouveaux)

- [ ] **Step 6: Enregistrer dans l'admin**

Ajouter à `checkin/admin.py` :

```python
from checkin.models import MembershipRequest


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "festival", "created_at"]
    list_filter = ["festival"]
```

- [ ] **Step 7: Appliquer la migration à la base de développement**

Run: `python manage.py migrate`
Expected: `Applying checkin.0007_membershiprequest... OK`

- [ ] **Step 8: Commit**

```bash
git add checkin/models.py checkin/admin.py checkin/migrations checkin/tests/test_models.py
git commit -m "feat: ajoute le modele MembershipRequest"
```

---

### Task 2: Bouton de déconnexion

**Files:**
- Modify: `checkin/templates/checkin/base.html`
- Modify: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: URL nommée `checkin:logout` (déjà existante).
- Produces: rien de nouveau consommé par d'autres tâches — modification purement visuelle du template de base.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views.py` (le fichier importe déjà `pytest`, `reverse`, `Festival`, `Membership`) :

```python
@pytest.mark.django_db
def test_base_template_shows_logout_button_when_authenticated(client, django_user_model):
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival_a, role=Membership.ROLE_BENEVOLE)
    Membership.objects.create(user=user, festival=festival_b, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 200
    assert 'action="/logout/"' in response.content.decode()


def test_login_page_does_not_show_logout_button(client):
    response = client.get(reverse("checkin:login"))
    assert response.status_code == 200
    assert 'action="/logout/"' not in response.content.decode()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v -k "logout_button"`
Expected: FAIL — `test_base_template_shows_logout_button_when_authenticated` échoue (pas de formulaire logout dans le HTML)

- [ ] **Step 3: Modifier le template de base**

Dans `checkin/templates/checkin/base.html`, remplacer :

```html
    {% if messages %}
    <ul class="messages">
        {% for message in messages %}
        <li class="message message--{{ message.tags }}">{{ message }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    <main>
```

par :

```html
    {% if messages %}
    <ul class="messages">
        {% for message in messages %}
        <li class="message message--{{ message.tags }}">{{ message }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    {% if user.is_authenticated %}
    <form method="post" action="{% url 'checkin:logout' %}" class="logout-form">
        {% csrf_token %}
        <button type="submit">Se déconnecter</button>
    </form>
    {% endif %}
    <main>
```

- [ ] **Step 4: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v -k "logout_button"`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add checkin/templates/checkin/base.html checkin/tests/test_views.py
git commit -m "feat: ajoute le bouton de deconnexion"
```

---

### Task 3: Inscription libre (`signup`)

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/signup.html`
- Modify: `checkin/templates/registration/login.html`
- Modify: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: `django.contrib.auth.forms.UserCreationForm`, `django.contrib.auth.login`.
- Produces: URL nommée `checkin:signup` (chemin `inscription/`), accessible sans connexion, redirige un utilisateur déjà connecté vers `checkin:select_festival`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views.py` :

```python
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_signup_creates_user_and_logs_in(client):
    response = client.post(
        reverse("checkin:signup"),
        {"username": "newuser", "password1": "un-mot-de-passe-solide-42", "password2": "un-mot-de-passe-solide-42"},
    )

    assert response.status_code == 302
    assert User.objects.filter(username="newuser").exists()
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_signup_rejects_duplicate_username(client, django_user_model):
    django_user_model.objects.create_user(username="bob", password="pass12345")

    response = client.post(
        reverse("checkin:signup"),
        {"username": "bob", "password1": "un-mot-de-passe-solide-42", "password2": "un-mot-de-passe-solide-42"},
    )

    assert response.status_code == 200
    assert User.objects.filter(username="bob").count() == 1


@pytest.mark.django_db
def test_signup_redirects_authenticated_user(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:signup"))

    assert response.status_code == 302
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v -k signup`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:signup` n'existe pas encore)

- [ ] **Step 3: Implémenter la vue**

Ajouter à `checkin/views.py` (en tête du fichier, ajouter les deux imports manquants à la liste existante) :

```python
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
```

Puis ajouter la vue (avant ou après `select_festival`) :

```python
def signup(request):
    if request.user.is_authenticated:
        return redirect("checkin:select_festival")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("checkin:select_festival")
    else:
        form = UserCreationForm()

    return render(request, "checkin/signup.html", {"form": form})
```

- [ ] **Step 4: Ajouter l'URL**

Modifier `checkin/urls.py`, ajouter avant `path("festivals/", ...)` :

```python
    path("inscription/", views.signup, name="signup"),
```

- [ ] **Step 5: Créer le template**

`checkin/templates/checkin/signup.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un compte — Festival Count{% endblock %}
{% block content %}
<h1>Créer un compte</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Créer mon compte</button>
</form>
{% endblock %}
```

- [ ] **Step 6: Ajouter le lien depuis la page de connexion**

Dans `checkin/templates/registration/login.html`, remplacer :

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Se connecter</button>
</form>
{% endblock %}
```

par :

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Se connecter</button>
</form>
<p><a href="{% url 'checkin:signup' %}">Créer un compte</a></p>
{% endblock %}
```

- [ ] **Step 7: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v -k signup`
Expected: `3 passed`

- [ ] **Step 8: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/signup.html checkin/templates/registration/login.html checkin/tests/test_views.py
git commit -m "feat: ajoute l'inscription libre"
```

---

### Task 4: Génération de slug unique + création de festival

**Files:**
- Modify: `checkin/selectors.py`
- Modify: `checkin/forms.py`
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/festival_create.html`
- Modify: `checkin/tests/test_selectors.py`
- Create: `checkin/tests/test_views_festivals.py`

**Interfaces:**
- Consumes: `checkin.models.Festival`, `checkin.models.Membership`.
- Produces: `checkin.selectors.generate_unique_festival_slug(nom) -> str`. `checkin.forms.FestivalCreationForm` (champ `nom`). URL nommée `checkin:festival_create` (chemin `festivals/creer/`), réservée aux utilisateurs connectés, crée un `Festival` + un `Membership` Organisateur pour l'utilisateur courant.

- [ ] **Step 1: Écrire les tests du sélecteur qui échouent**

Dans `checkin/tests/test_selectors.py`, `Festival` est déjà importé ; remplacer la ligne d'import existante :

```python
from checkin.selectors import get_active_edition
```

par :

```python
from checkin.selectors import generate_unique_festival_slug, get_active_edition
```

Puis ajouter les tests :

```python
@pytest.mark.django_db
def test_generate_unique_festival_slug_from_name():
    slug = generate_unique_festival_slug("Festival Photo de Tignecourt")
    assert slug == "festival-photo-de-tignecourt"


@pytest.mark.django_db
def test_generate_unique_festival_slug_adds_suffix_on_collision():
    Festival.objects.create(nom="Festival A", slug="festival-a")
    slug = generate_unique_festival_slug("Festival A")
    assert slug == "festival-a-2"


@pytest.mark.django_db
def test_generate_unique_festival_slug_increments_suffix_further():
    Festival.objects.create(nom="Festival A", slug="festival-a")
    Festival.objects.create(nom="Festival A bis", slug="festival-a-2")
    slug = generate_unique_festival_slug("Festival A")
    assert slug == "festival-a-3"
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_selectors.py -v`
Expected: FAIL — `ImportError: cannot import name 'generate_unique_festival_slug' from 'checkin.selectors'`

- [ ] **Step 3: Implémenter le sélecteur**

Ajouter à `checkin/selectors.py` :

```python
from django.utils.text import slugify

from checkin.models import Festival


def generate_unique_festival_slug(nom):
    base_slug = slugify(nom)
    slug = base_slug
    counter = 1
    while Festival.objects.filter(slug=slug).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug
```

- [ ] **Step 4: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_selectors.py -v`
Expected: `6 passed`

- [ ] **Step 5: Écrire les tests de la vue qui échouent**

`checkin/tests/test_views_festivals.py` :

```python
import pytest
from django.urls import reverse

from checkin.models import Festival, Membership


@pytest.mark.django_db
def test_festival_create_requires_login(client):
    response = client.get(reverse("checkin:festival_create"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_festival_create_creates_festival_and_organisateur_membership(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.post(reverse("checkin:festival_create"), {"nom": "Festival Photo de Tignecourt"})

    assert response.status_code == 302
    festival = Festival.objects.get(nom="Festival Photo de Tignecourt")
    assert festival.slug == "festival-photo-de-tignecourt"
    membership = Membership.objects.get(user=user, festival=festival)
    assert membership.role == Membership.ROLE_ORGANISATEUR


@pytest.mark.django_db
def test_festival_create_generates_unique_slug_on_name_collision(client, django_user_model):
    Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.post(reverse("checkin:festival_create"), {"nom": "Festival A"})

    assert response.status_code == 302
    new_festival = Festival.objects.get(nom="Festival A", slug="festival-a-2")
    assert Membership.objects.filter(user=user, festival=new_festival).exists()
```

- [ ] **Step 6: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_festivals.py -v`
Expected: FAIL — `NoReverseMatch` (l'URL `checkin:festival_create` n'existe pas encore)

- [ ] **Step 7: Ajouter le formulaire**

Ajouter à `checkin/forms.py` :

```python
class FestivalCreationForm(forms.Form):
    nom = forms.CharField(max_length=200)
```

- [ ] **Step 8: Implémenter la vue**

Dans `checkin/views.py`, remplacer les trois lignes d'import suivantes :

```python
from checkin.forms import EditionForm, VolunteerCreationForm
from checkin.models import Membership, Origin, Visit
from checkin.selectors import get_active_edition
```

par :

```python
from checkin.forms import EditionForm, FestivalCreationForm, VolunteerCreationForm
from checkin.models import Festival, Membership, Origin, Visit
from checkin.selectors import generate_unique_festival_slug, get_active_edition
```

Puis ajouter la vue :

```python
@login_required
def festival_create(request):
    if request.method == "POST":
        form = FestivalCreationForm(request.POST)
        if form.is_valid():
            nom = form.cleaned_data["nom"]
            slug = generate_unique_festival_slug(nom)
            festival = Festival.objects.create(nom=nom, slug=slug)
            Membership.objects.create(user=request.user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
            messages.success(request, f"Festival « {festival.nom} » créé avec succès.")
            return redirect("checkin:stats", festival_slug=festival.slug)
    else:
        form = FestivalCreationForm()

    return render(request, "checkin/festival_create.html", {"form": form})
```

- [ ] **Step 9: Ajouter l'URL**

Modifier `checkin/urls.py`, ajouter juste après `path("festivals/", ...)` :

```python
    path("festivals/creer/", views.festival_create, name="festival_create"),
```

- [ ] **Step 10: Créer le template**

`checkin/templates/checkin/festival_create.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Créer un festival — Festival Count{% endblock %}
{% block content %}
<h1>Créer un festival</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Créer</button>
</form>
{% endblock %}
```

- [ ] **Step 11: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_festivals.py -v`
Expected: `3 passed`

- [ ] **Step 12: Commit**

```bash
git add checkin/selectors.py checkin/forms.py checkin/views.py checkin/urls.py checkin/templates/checkin/festival_create.html checkin/tests/test_selectors.py checkin/tests/test_views_festivals.py
git commit -m "feat: ajoute la creation de festival en self-service"
```

---

### Task 5: Recherche de festival + demande d'adhésion

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/templates/checkin/festival_search.html`
- Modify: `checkin/tests/test_views_festivals.py`

**Interfaces:**
- Consumes: `checkin.models.MembershipRequest`, `checkin.models.Festival`, `checkin.models.Membership`.
- Produces: URL nommée `checkin:festival_search` (chemin `festivals/rejoindre/`, GET avec paramètre `q`) ; URL nommée `checkin:membership_request_create` (chemin `f/<slug:festival_slug>/rejoindre/`, POST).

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `checkin/tests/test_views_festivals.py` :

```python
from checkin.models import MembershipRequest


@pytest.mark.django_db
def test_festival_search_excludes_festivals_already_member(client, django_user_model):
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:festival_search"), {"q": "Photo"})

    assert response.status_code == 200
    assert "Festival Photo" not in response.content.decode()


@pytest.mark.django_db
def test_festival_search_shows_matching_festivals(client, django_user_model):
    Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:festival_search"), {"q": "Tignecourt"})

    assert response.status_code == 200
    assert "Festival Photo de Tignecourt" in response.content.decode()


@pytest.mark.django_db
def test_festival_search_shows_pending_status(client, django_user_model):
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    MembershipRequest.objects.create(user=user, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:festival_search"), {"q": "Photo"})

    assert response.status_code == 200
    assert "Demande envoyée" in response.content.decode()


@pytest.mark.django_db
def test_membership_request_create_creates_a_request(client, django_user_model):
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.post(reverse("checkin:membership_request_create", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302
    assert MembershipRequest.objects.filter(user=user, festival=festival).exists()


@pytest.mark.django_db
def test_membership_request_create_rejects_duplicate(client, django_user_model):
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    MembershipRequest.objects.create(user=user, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.post(reverse("checkin:membership_request_create", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302
    assert MembershipRequest.objects.filter(user=user, festival=festival).count() == 1


@pytest.mark.django_db
def test_membership_request_create_rejects_if_already_member(client, django_user_model):
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(reverse("checkin:membership_request_create", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302
    assert not MembershipRequest.objects.filter(user=user, festival=festival).exists()
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_festivals.py -v -k "search or membership_request"`
Expected: FAIL — `NoReverseMatch` (les URLs n'existent pas encore)

- [ ] **Step 3: Implémenter les vues**

Dans `checkin/views.py`, remplacer la ligne d'import :

```python
from django.shortcuts import redirect, render
```

par :

```python
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
```

Puis remplacer la ligne d'import des modèles (établie par la Task 4) :

```python
from checkin.models import Festival, Membership, Origin, Visit
```

par :

```python
from checkin.models import Festival, Membership, MembershipRequest, Origin, Visit
```

Puis ajouter les vues :

```python
@login_required
def festival_search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        member_festival_ids = Membership.objects.filter(user=request.user).values_list("festival_id", flat=True)
        pending_festival_ids = set(
            MembershipRequest.objects.filter(user=request.user).values_list("festival_id", flat=True)
        )
        festivals = Festival.objects.filter(nom__icontains=query).exclude(id__in=member_festival_ids)
        results = [
            {"festival": festival, "pending": festival.id in pending_festival_ids}
            for festival in festivals
        ]

    return render(request, "checkin/festival_search.html", {"query": query, "results": results})


@require_POST
@login_required
def membership_request_create(request, festival_slug):
    festival = get_object_or_404(Festival, slug=festival_slug)

    if Membership.objects.filter(user=request.user, festival=festival).exists():
        messages.error(request, "Vous êtes déjà membre de ce festival.")
    elif MembershipRequest.objects.filter(user=request.user, festival=festival).exists():
        messages.info(request, "Votre demande est déjà en attente.")
    else:
        MembershipRequest.objects.create(user=request.user, festival=festival)
        messages.success(request, "Demande envoyée. L'organisateur doit encore la valider.")

    query = request.POST.get("q", "")
    return redirect(f"{reverse('checkin:festival_search')}?q={query}")
```

- [ ] **Step 4: Ajouter les URLs**

Modifier `checkin/urls.py`, ajouter juste après `path("festivals/creer/", ...)` :

```python
    path("festivals/rejoindre/", views.festival_search, name="festival_search"),
```

Et ajouter juste après `path("f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/", ...)` (n'importe où dans le groupe des URLs `f/<slug:festival_slug>/...` convient) :

```python
    path("f/<slug:festival_slug>/rejoindre/", views.membership_request_create, name="membership_request_create"),
```

- [ ] **Step 5: Créer le template**

`checkin/templates/checkin/festival_search.html` :

```html
{% extends "checkin/base.html" %}
{% block title %}Rejoindre un festival — Festival Count{% endblock %}
{% block content %}
<h1>Rejoindre un festival</h1>
<form method="get">
    <input type="text" name="q" value="{{ query }}" placeholder="Nom du festival">
    <button type="submit">Rechercher</button>
</form>

<ul>
    {% for result in results %}
    <li>
        {{ result.festival.nom }}
        {% if result.pending %}
        <span>Demande envoyée</span>
        {% else %}
        <form method="post" action="{% url 'checkin:membership_request_create' festival_slug=result.festival.slug %}" style="display:inline">
            {% csrf_token %}
            <input type="hidden" name="q" value="{{ query }}">
            <button type="submit">Demander à rejoindre</button>
        </form>
        {% endif %}
    </li>
    {% endfor %}
</ul>
{% endblock %}
```

- [ ] **Step 6: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_festivals.py -v`
Expected: `9 passed`

- [ ] **Step 7: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/templates/checkin/festival_search.html checkin/tests/test_views_festivals.py
git commit -m "feat: ajoute la recherche et la demande d'adhesion a un festival"
```

---

### Task 6: Liens « Créer un festival » / « Rejoindre un festival » sur le tableau de bord

**Files:**
- Modify: `checkin/templates/checkin/select_festival.html`
- Modify: `checkin/tests/test_views.py`

**Interfaces:**
- Consumes: URLs `checkin:festival_create` (Task 4) et `checkin:festival_search` (Task 5).
- Produces: rien de nouveau consommé par d'autres tâches.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à `checkin/tests/test_views.py` :

```python
@pytest.mark.django_db
def test_select_festival_always_shows_create_and_join_links(client, django_user_model):
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival_a, role=Membership.ROLE_BENEVOLE)
    Membership.objects.create(user=user, festival=festival_b, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert response.status_code == 200
    content = response.content.decode()
    assert reverse("checkin:festival_create") in content
    assert reverse("checkin:festival_search") in content
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `pytest checkin/tests/test_views.py -v -k always_shows_create_and_join`
Expected: FAIL — les liens ne sont pas présents dans le HTML

- [ ] **Step 3: Modifier le template**

Dans `checkin/templates/checkin/select_festival.html`, remplacer :

```html
{% else %}
<p>Vous n'avez accès à aucun festival pour le moment. Contactez l'organisateur de votre festival.</p>
{% endif %}
{% endblock %}
```

par :

```html
{% else %}
<p>Vous n'avez accès à aucun festival pour le moment.</p>
{% endif %}

<p><a href="{% url 'checkin:festival_create' %}">Créer un festival</a></p>
<p><a href="{% url 'checkin:festival_search' %}">Rejoindre un festival</a></p>
{% endblock %}
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `pytest checkin/tests/test_views.py -v -k always_shows_create_and_join`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add checkin/templates/checkin/select_festival.html checkin/tests/test_views.py
git commit -m "feat: affiche les liens creer/rejoindre un festival sur le tableau de bord"
```

---

### Task 7: Acceptation et refus des demandes d'adhésion

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/urls.py`
- Create: `checkin/tests/test_views_membership_requests.py`

**Interfaces:**
- Consumes: `checkin.models.MembershipRequest`, `checkin.permissions.membership_required`.
- Produces: URLs nommées `checkin:membership_request_accept` et `checkin:membership_request_reject` (chemins `f/<slug:festival_slug>/benevoles/demandes/<int:request_id>/accepter/` et `.../refuser/`), réservées aux organisateurs du festival concerné.

- [ ] **Step 1: Écrire les tests qui échouent**

`checkin/tests/test_views_membership_requests.py` :

```python
import pytest
from django.urls import reverse

from checkin.models import Festival, Membership, MembershipRequest


@pytest.mark.django_db
def test_membership_request_accept_creates_membership(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse(
            "checkin:membership_request_accept",
            kwargs={"festival_slug": festival.slug, "request_id": membership_request.id},
        )
    )

    assert response.status_code == 302
    assert Membership.objects.filter(user=requester, festival=festival, role=Membership.ROLE_BENEVOLE).exists()
    assert not MembershipRequest.objects.filter(id=membership_request.id).exists()


@pytest.mark.django_db
def test_membership_request_reject_deletes_request(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse(
            "checkin:membership_request_reject",
            kwargs={"festival_slug": festival.slug, "request_id": membership_request.id},
        )
    )

    assert response.status_code == 302
    assert not MembershipRequest.objects.filter(id=membership_request.id).exists()
    assert not Membership.objects.filter(user=requester, festival=festival).exists()


@pytest.mark.django_db
def test_membership_request_accept_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    benevole = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=benevole, festival=festival, role=Membership.ROLE_BENEVOLE)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse(
            "checkin:membership_request_accept",
            kwargs={"festival_slug": festival.slug, "request_id": membership_request.id},
        )
    )

    assert response.status_code == 302
    assert MembershipRequest.objects.filter(id=membership_request.id).exists()


@pytest.mark.django_db
def test_membership_request_accept_is_noop_when_already_processed(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse(
            "checkin:membership_request_accept",
            kwargs={"festival_slug": festival.slug, "request_id": 9999},
        )
    )

    assert response.status_code == 302
```

- [ ] **Step 2: Lancer les tests, vérifier l'échec**

Run: `pytest checkin/tests/test_views_membership_requests.py -v`
Expected: FAIL — `NoReverseMatch` (les URLs n'existent pas encore)

- [ ] **Step 3: Implémenter les vues**

Ajouter à `checkin/views.py` :

```python
@require_POST
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def membership_request_accept(request, festival_slug, request_id):
    membership_request = MembershipRequest.objects.filter(id=request_id, festival=request.festival).first()
    if membership_request is not None:
        Membership.objects.create(
            user=membership_request.user, festival=request.festival, role=Membership.ROLE_BENEVOLE
        )
        membership_request.delete()
        messages.success(request, "Demande acceptée.")
    return redirect("checkin:volunteer_list", festival_slug=festival_slug)


@require_POST
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def membership_request_reject(request, festival_slug, request_id):
    MembershipRequest.objects.filter(id=request_id, festival=request.festival).delete()
    messages.success(request, "Demande refusée.")
    return redirect("checkin:volunteer_list", festival_slug=festival_slug)
```

- [ ] **Step 4: Ajouter les URLs**

Modifier `checkin/urls.py`, ajouter juste après `path("f/<slug:festival_slug>/benevoles/", ...)` :

```python
    path(
        "f/<slug:festival_slug>/benevoles/demandes/<int:request_id>/accepter/",
        views.membership_request_accept,
        name="membership_request_accept",
    ),
    path(
        "f/<slug:festival_slug>/benevoles/demandes/<int:request_id>/refuser/",
        views.membership_request_reject,
        name="membership_request_reject",
    ),
```

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_membership_requests.py -v`
Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add checkin/views.py checkin/urls.py checkin/tests/test_views_membership_requests.py
git commit -m "feat: ajoute l'acceptation et le refus des demandes d'adhesion"
```

---

### Task 8: Affichage des demandes en attente sur la page Bénévoles

**Files:**
- Modify: `checkin/views.py`
- Modify: `checkin/templates/checkin/volunteer_list.html`
- Modify: `checkin/tests/test_views_volunteers.py`

**Interfaces:**
- Consumes: `checkin.models.MembershipRequest`, URLs `checkin:membership_request_accept`/`checkin:membership_request_reject` (Task 7).
- Produces: contexte de template `pending_requests` (queryset de `MembershipRequest` du festival) consommé par `volunteer_list.html`.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à `checkin/tests/test_views_volunteers.py` :

```python
from checkin.models import MembershipRequest


@pytest.mark.django_db
def test_volunteer_list_shows_pending_requests(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert "bob" in response.content.decode()
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `pytest checkin/tests/test_views_volunteers.py -v -k pending_requests`
Expected: FAIL — `bob` n'apparaît pas dans la page (pas encore affiché)

- [ ] **Step 3: Mettre à jour la vue**

Remplacer dans `checkin/views.py` la fonction `volunteer_list` par :

```python
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def volunteer_list(request, festival_slug):
    memberships = Membership.objects.filter(
        festival=request.festival, role=Membership.ROLE_BENEVOLE
    ).select_related("user")
    pending_requests = MembershipRequest.objects.filter(festival=request.festival).select_related("user")

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

    return render(
        request,
        "checkin/volunteer_list.html",
        {"memberships": memberships, "pending_requests": pending_requests, "form": form},
    )
```

- [ ] **Step 4: Mettre à jour le template**

Remplacer le contenu de `checkin/templates/checkin/volunteer_list.html` par :

```html
{% extends "checkin/base.html" %}
{% block title %}Bénévoles — {{ request.festival.nom }}{% endblock %}
{% block content %}
<h1>{{ request.festival.nom }} — Bénévoles</h1>

<h2>Demandes en attente</h2>
<ul>
    {% for membership_request in pending_requests %}
    <li>
        {{ membership_request.user.username }}
        <form method="post" action="{% url 'checkin:membership_request_accept' festival_slug=request.festival.slug request_id=membership_request.id %}" style="display:inline">
            {% csrf_token %}
            <button type="submit">Accepter</button>
        </form>
        <form method="post" action="{% url 'checkin:membership_request_reject' festival_slug=request.festival.slug request_id=membership_request.id %}" style="display:inline">
            {% csrf_token %}
            <button type="submit">Refuser</button>
        </form>
    </li>
    {% endfor %}
</ul>

<h2>Bénévoles</h2>
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

- [ ] **Step 5: Lancer les tests, vérifier le succès**

Run: `pytest checkin/tests/test_views_volunteers.py -v`
Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git add checkin/views.py checkin/templates/checkin/volunteer_list.html checkin/tests/test_views_volunteers.py
git commit -m "feat: affiche les demandes d'adhesion en attente sur la page benevoles"
```

---

### Task 9: Vérification finale (suite complète + navigateur) et mise à jour du README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: l'ensemble des tâches précédentes.
- Produces: documentation à jour ; aucune interface de code.

- [ ] **Step 1: Lancer la suite de tests complète**

Run: `pytest -v`
Expected: tous les tests passent, aucun `FAILED` dans la sortie.

- [ ] **Step 2: Mettre à jour le README**

Dans `README.md`, remplacer la section « Création d'un festival (première fois) » par :

```markdown
## Créer un compte et un festival

1. Lancer `python manage.py runserver`, ouvrir `/inscription/` et créer un compte.
2. Depuis le tableau de bord, cliquer sur « Créer un festival » (le slug est généré automatiquement à partir du nom) : vous devenez Organisateur de ce festival.
3. Depuis la page « Éditions » du festival, créer une édition (nom + dates du week-end du festival).
4. Les bénévoles créent eux-mêmes un compte via `/inscription/`, puis « Rejoindre un festival » pour envoyer une demande — à valider depuis la page « Bénévoles » du festival. Un organisateur peut aussi créer directement un compte bénévole depuis cette même page.

Le compte superuser Django (`createsuperuser` + `/admin/`) reste utile pour l'administration technique (suppression de données, etc.) mais n'est plus nécessaire pour créer le premier festival.
```

- [ ] **Step 3: Vérification manuelle dans un navigateur (Playwright)**

Prérequis : lancer le serveur de développement en arrière-plan sur un port libre, par exemple :

Run: `python manage.py runserver 127.0.0.1:8001 --noreload` (en arrière-plan)

Avec les outils `mcp__playwright__browser_navigate`, `browser_click`, `browser_fill_form`, `browser_type`, `browser_snapshot` (charger leurs schémas via ToolSearch si besoin), dérouler le parcours suivant sur `http://127.0.0.1:8001` :

1. Naviguer vers `/login/` → vérifier le lien « Créer un compte » → cliquer dessus.
2. Sur `/inscription/`, créer un compte (ex. `verif_organisateur` / un mot de passe respectant les règles de robustesse) → vérifier la redirection vers le tableau de bord avec les liens « Créer un festival » et « Rejoindre un festival », et la présence du bouton « Se déconnecter ».
3. Cliquer « Créer un festival », saisir un nom, valider → vérifier l'arrivée sur la page de statistiques du nouveau festival.
4. Cliquer « Se déconnecter » → vérifier le retour à `/login/`.
5. Créer un second compte (ex. `verif_benevole`) via `/inscription/` → sur le tableau de bord, cliquer « Rejoindre un festival », rechercher le nom du festival créé à l'étape 3, cliquer « Demander à rejoindre » → vérifier que le bouton devient « Demande envoyée ».
6. Se reconnecter avec `verif_organisateur` → aller sur la page « Bénévoles » du festival → vérifier que la demande de `verif_benevole` apparaît dans « Demandes en attente » → cliquer « Accepter » → vérifier qu'il apparaît maintenant dans la liste des bénévoles et que la demande a disparu.
7. Se reconnecter avec `verif_benevole` → vérifier l'accès direct à la page d'enregistrement de ce festival (auto-redirection, un seul festival).

Nettoyer ensuite les comptes et le festival de test créés (via `python manage.py shell`, comme pour les vérifications précédentes), puis relancer `pytest -v` pour confirmer l'absence de régression.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: met a jour le README pour l'inscription libre"
```

---
