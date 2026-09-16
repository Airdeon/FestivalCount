import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin


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
