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
