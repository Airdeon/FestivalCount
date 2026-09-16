import datetime

import pytest

from checkin.models import Edition, Festival
from checkin.selectors import get_active_edition


@pytest.mark.django_db
def test_get_active_edition_returns_edition_within_dates():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)

    assert get_active_edition(festival) == edition


@pytest.mark.django_db
def test_get_active_edition_returns_none_when_no_active_edition():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(
        festival=festival, nom="2025",
        date_debut=today - datetime.timedelta(days=10),
        date_fin=today - datetime.timedelta(days=8),
    )

    assert get_active_edition(festival) is None


@pytest.mark.django_db
def test_get_active_edition_ignores_other_festivals():
    festival_a = Festival.objects.create(nom="Festival A", slug="festival-a")
    festival_b = Festival.objects.create(nom="Festival B", slug="festival-b")
    today = datetime.date.today()
    Edition.objects.create(festival=festival_b, nom="2026", date_debut=today, date_fin=today)

    assert get_active_edition(festival_a) is None
