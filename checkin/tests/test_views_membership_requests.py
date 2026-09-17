from unittest.mock import patch

import pytest
from django.db import IntegrityError
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


@pytest.mark.django_db
def test_membership_request_accept_handles_race_condition(client, django_user_model):
    """Test that IntegrityError from concurrent accepts is handled gracefully."""
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    with patch(
        "checkin.models.Membership.objects.create",
        side_effect=IntegrityError("Unique constraint violated"),
    ):
        response = client.post(
            reverse(
                "checkin:membership_request_accept",
                kwargs={"festival_slug": festival.slug, "request_id": membership_request.id},
            )
        )

    # Verify we get a 302 redirect (not 500)
    assert response.status_code == 302
    # Verify the request was deleted (cleaned up as redundant)
    assert not MembershipRequest.objects.filter(id=membership_request.id).exists()


@pytest.mark.django_db
def test_membership_request_reject_is_silent_noop_when_already_processed(client, django_user_model):
    """Test that rejecting a nonexistent request is a silent no-op."""
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    # Attempt to reject a request that doesn't exist (e.g., already processed)
    response = client.post(
        reverse(
            "checkin:membership_request_reject",
            kwargs={"festival_slug": festival.slug, "request_id": 99999},
        )
    )

    # Verify we get a 302 redirect without error
    assert response.status_code == 302
    # Verify no request with that id exists
    assert not MembershipRequest.objects.filter(id=99999).exists()
