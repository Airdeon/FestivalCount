from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.db import IntegrityError
from django.urls import reverse

from checkin.models import Festival, Membership, MembershipRequest


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


@pytest.mark.django_db
def test_membership_request_create_handles_race_condition(
    client, django_user_model
):
    """Test that IntegrityError from concurrent requests is handled."""
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(
        username="alice", password="pass12345"
    )
    client.login(username="alice", password="pass12345")

    with patch(
        "checkin.models.MembershipRequest.objects.create",
        side_effect=IntegrityError("Unique constraint violated"),
    ):
        response = client.post(
            reverse(
                "checkin:membership_request_create",
                kwargs={"festival_slug": festival.slug},
            )
        )

    # Verify we get a 302 redirect (not 500)
    assert response.status_code == 302
    # Verify no request was created (due to patched exception)
    assert not MembershipRequest.objects.filter(
        user=user, festival=festival
    ).exists()


@pytest.mark.django_db
def test_membership_request_create_encodes_query_parameter(client, django_user_model):
    """Test that special characters in search query are URL-encoded in the redirect."""
    festival = Festival.objects.create(nom="Festival Photo", slug="festival-photo")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    # POST with a query parameter containing special characters
    original_query = "test & special + chars#hash"
    response = client.post(
        reverse("checkin:membership_request_create", kwargs={"festival_slug": festival.slug}),
        {"q": original_query},
    )

    # Verify redirect (302)
    assert response.status_code == 302
    # Verify the URL-encoded query parameter round-trips correctly
    assert response.url is not None
    parsed_qs = parse_qs(urlparse(response.url).query)
    # The query parameter should be properly decoded and match the original value
    assert parsed_qs["q"] == [original_query]


@pytest.mark.django_db
def test_festival_create_handles_race_condition(client, django_user_model):
    """Test that IntegrityError from concurrent festival creates is handled gracefully."""
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    client.login(username="alice", password="pass12345")

    # Mock the create method to fail on first call, then call the real create on retry
    real_create = Festival.objects.create
    call_count = {"n": 0}

    def fake_create(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise IntegrityError("Unique constraint violated")
        return real_create(*args, **kwargs)

    with patch("checkin.models.Festival.objects.create", side_effect=fake_create):
        response = client.post(
            reverse("checkin:festival_create"),
            {"nom": "Test Festival"},
        )

    # Verify we get a 302 redirect (not 500)
    assert response.status_code == 302
    # Verify exactly one Festival exists (the retry's create() call actually persisted a row)
    assert Festival.objects.count() == 1
    # Verify the organizer membership was created
    assert Membership.objects.filter(user=user, role=Membership.ROLE_ORGANISATEUR).count() == 1
