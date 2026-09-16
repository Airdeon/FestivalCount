import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin, Visit


@pytest.mark.django_db
def test_stats_data_returns_json_for_organisateur(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.get(code="75")
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
