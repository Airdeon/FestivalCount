import pytest

from checkin.models import Festival


@pytest.mark.django_db
def test_festival_str_returns_nom():
    festival = Festival.objects.create(nom="Festival Photo de Tignecourt", slug="festival-photo-tignecourt")
    assert str(festival) == "Festival Photo de Tignecourt"


@pytest.mark.django_db
def test_festival_slug_is_unique():
    Festival.objects.create(nom="Festival A", slug="meme-slug")
    with pytest.raises(Exception):
        Festival.objects.create(nom="Festival B", slug="meme-slug")
