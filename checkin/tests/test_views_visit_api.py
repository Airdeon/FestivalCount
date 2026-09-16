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
    origin = Origin.objects.get(code="75")
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


@pytest.mark.django_db
def test_visit_cancel_deletes_the_visit(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.get(code="75")
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
    origin = Origin.objects.get(code="75")
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
