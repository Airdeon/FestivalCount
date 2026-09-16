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
