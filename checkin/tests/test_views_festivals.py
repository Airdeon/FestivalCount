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
