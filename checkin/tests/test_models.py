import datetime

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from checkin.models import Edition, Festival, Membership, MembershipRequest, Origin, Visit


@pytest.mark.django_db
def test_festival_str_returns_nom():
    festival = Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    assert str(festival) == "Festival Photo de Tignecourt"


@pytest.mark.django_db
def test_festival_slug_is_unique():
    Festival.objects.create(nom="Festival A", slug="meme-slug")
    with pytest.raises(Exception):
        Festival.objects.create(nom="Festival B", slug="meme-slug")


@pytest.mark.django_db
def test_edition_est_active_true_when_today_within_dates():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2026",
        date_debut=today - datetime.timedelta(days=1),
        date_fin=today + datetime.timedelta(days=1),
    )
    assert edition.est_active is True


@pytest.mark.django_db
def test_edition_est_active_false_when_dates_are_in_the_past():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2025",
        date_debut=today - datetime.timedelta(days=10),
        date_fin=today - datetime.timedelta(days=8),
    )
    assert edition.est_active is False


@pytest.mark.django_db
def test_edition_est_active_false_when_dates_are_in_the_future():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(
        festival=festival,
        nom="Édition 2027",
        date_debut=today + datetime.timedelta(days=8),
        date_fin=today + datetime.timedelta(days=10),
    )
    assert edition.est_active is False


@pytest.mark.django_db
def test_membership_str_includes_role_label():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    membership = Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    assert "alice" in str(membership)
    assert "Festival A" in str(membership)


@pytest.mark.django_db
def test_membership_is_unique_per_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)


@pytest.mark.django_db
def test_origin_str_includes_code_and_nom():
    origin = Origin.objects.create(
        code="99", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1
    )
    assert "99" in str(origin)
    assert "Paris" in str(origin)


@pytest.mark.django_db
def test_origin_code_is_unique():
    Origin.objects.create(code="99", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    with pytest.raises(Exception):
        Origin.objects.create(code="99", nom="Doublon", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=2)


@pytest.mark.django_db
def test_visit_records_horodatage_automatically():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    edition = Edition.objects.create(
        festival=festival, nom="Édition 2026",
        date_debut=datetime.date.today(), date_fin=datetime.date.today(),
    )
    origin = Origin.objects.create(code="99", nom="Paris", type=Origin.TYPE_DEPARTEMENT, groupe="60–79", ordre_affichage=1)
    user = User.objects.create_user(username="alice", password="pass12345")

    visit = Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)

    assert visit.horodatage is not None


@pytest.mark.django_db
def test_visit_precision_libre_is_optional():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    edition = Edition.objects.create(
        festival=festival, nom="Édition 2026",
        date_debut=datetime.date.today(), date_fin=datetime.date.today(),
    )
    origin = Origin.objects.create(code="ZZ", nom="Autre pays", type=Origin.TYPE_AUTRE, groupe="Étranger", ordre_affichage=1)
    user = User.objects.create_user(username="alice", password="pass12345")

    visit = Visit.objects.create(edition=edition, origin=origin, enregistre_par=user, precision_libre="Canada")

    assert visit.precision_libre == "Canada"


@pytest.mark.django_db
def test_membership_request_str_includes_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    membership_request = MembershipRequest.objects.create(user=user, festival=festival)
    assert "alice" in str(membership_request)
    assert "Festival A" in str(membership_request)


@pytest.mark.django_db
def test_membership_request_is_unique_per_user_and_festival():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = User.objects.create_user(username="alice", password="pass12345")
    MembershipRequest.objects.create(user=user, festival=festival)
    with pytest.raises(IntegrityError):
        MembershipRequest.objects.create(user=user, festival=festival)
