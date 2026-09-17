import datetime

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin


@pytest.mark.django_db
def test_select_festival_requires_login(client):
    response = client.get(reverse("checkin:select_festival"))
    assert response.status_code == 302


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


@pytest.mark.django_db
def test_select_festival_shows_message_when_no_memberships(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:select_festival"))

    assert "aucun festival" in response.content.decode()


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
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert Origin.objects.filter(code="75").exists()
    assert "Paris" in response.content.decode()


@pytest.mark.django_db
def test_register_denies_access_without_membership(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:register", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


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
