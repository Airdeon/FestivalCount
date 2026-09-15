import datetime

import pytest

from checkin.models import Edition, Festival


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
