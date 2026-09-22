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


@pytest.mark.django_db
def test_edition_list_shows_back_link_to_stats(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:stats", kwargs={"festival_slug": festival.slug}) in response.content.decode()
