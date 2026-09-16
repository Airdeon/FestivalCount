import pytest

from checkin.models import Origin
from checkin.reference_data import GROUPE_DOM_TOM, GROUPE_ETRANGER, ORIGINS


def test_origins_reference_data_has_112_entries():
    assert len(ORIGINS) == 112


def test_origins_reference_data_codes_are_unique():
    codes = [entry["code"] for entry in ORIGINS]
    assert len(codes) == len(set(codes))


def test_origins_reference_data_includes_autre_pays():
    autre = [entry for entry in ORIGINS if entry["code"] == "AUTRE"]
    assert len(autre) == 1
    assert autre[0]["type"] == Origin.TYPE_AUTRE
    assert autre[0]["groupe"] == GROUPE_ETRANGER


@pytest.mark.django_db
def test_migration_populates_112_origins():
    assert Origin.objects.count() == 112


@pytest.mark.django_db
def test_migration_populates_101_departements_et_dom_tom():
    count = Origin.objects.filter(type__in=[Origin.TYPE_DEPARTEMENT, Origin.TYPE_DOM_TOM]).count()
    assert count == 101


@pytest.mark.django_db
def test_migration_populates_dom_tom_group_with_5_entries():
    assert Origin.objects.filter(groupe=GROUPE_DOM_TOM).count() == 5
