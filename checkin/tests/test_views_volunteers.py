import pytest
from django.urls import reverse

from checkin.models import Festival, Membership, MembershipRequest


@pytest.mark.django_db
def test_volunteer_list_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_volunteer_list_creates_a_volunteer_account(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}),
        {"username": "bob", "password": "pass67890"},
    )

    assert response.status_code == 302
    new_membership = Membership.objects.get(user__username="bob", festival=festival)
    assert new_membership.role == Membership.ROLE_BENEVOLE
    assert new_membership.user.check_password("pass67890")


@pytest.mark.django_db
def test_volunteer_list_rejects_duplicate_username(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    django_user_model.objects.create_user(username="bob", password="pass12345")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}),
        {"username": "bob", "password": "pass67890"},
    )

    assert response.status_code == 200
    assert Membership.objects.filter(festival=festival, user__username="bob").count() == 0


@pytest.mark.django_db
def test_volunteer_remove_deletes_membership(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    volunteer_user = django_user_model.objects.create_user(username="bob", password="pass12345")
    volunteer_membership = Membership.objects.create(user=volunteer_user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.post(
        reverse("checkin:volunteer_remove", kwargs={"festival_slug": festival.slug, "membership_id": volunteer_membership.id})
    )

    assert response.status_code == 302
    assert not Membership.objects.filter(id=volunteer_membership.id).exists()
    assert django_user_model.objects.filter(username="bob").exists()


@pytest.mark.django_db
def test_volunteer_list_shows_pending_requests(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    organisateur = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=organisateur, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    requester = django_user_model.objects.create_user(username="bob", password="pass12345")
    MembershipRequest.objects.create(user=requester, festival=festival)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert "bob" in response.content.decode()
