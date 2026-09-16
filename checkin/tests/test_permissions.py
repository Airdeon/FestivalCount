import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from checkin.models import Festival, Membership
from checkin.permissions import membership_required


def _prepare_request(request):
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)
    return request


@membership_required()
def _any_role_view(request, festival_slug):
    return HttpResponse("ok")


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def _organisateur_only_view(request, festival_slug):
    return HttpResponse("ok")


@pytest.mark.django_db
def test_membership_required_allows_access_for_any_role():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 200
    assert request.festival == festival
    assert request.membership.role == Membership.ROLE_BENEVOLE


@pytest.mark.django_db
def test_membership_required_redirects_when_no_membership():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 302
    assert response.url == "/festivals/"


@pytest.mark.django_db
def test_membership_required_redirects_when_role_not_allowed():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = user

    response = _organisateur_only_view(request, festival_slug=festival.slug)

    assert response.status_code == 302


@pytest.mark.django_db
def test_membership_required_redirects_anonymous_user_to_login():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    request = _prepare_request(RequestFactory().get(f"/f/{festival.slug}/dummy/"))
    request.user = AnonymousUser()

    response = _any_role_view(request, festival_slug=festival.slug)

    assert response.status_code == 302
    assert "/login/" in response.url
