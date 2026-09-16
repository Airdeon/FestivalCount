import datetime

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from checkin.models import Edition, Festival, Origin, Visit
from checkin.stats import get_hourly_evolution, get_key_figures, get_ranking


@pytest.mark.django_db
def test_get_key_figures_counts_total_and_distinct_origins():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.get(code="75")
    rhone = Origin.objects.get(code="69")
    belgique = Origin.objects.get(code="BE")

    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=belgique, enregistre_par=user)

    figures = get_key_figures(edition)

    assert figures["total_visiteurs"] == 4
    assert figures["nombre_departements"] == 2
    assert figures["nombre_pays"] == 1


@pytest.mark.django_db
def test_get_key_figures_ignores_other_editions():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition_a = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    edition_b = Edition.objects.create(
        festival=festival, nom="2025",
        date_debut=today - datetime.timedelta(days=365),
        date_fin=today - datetime.timedelta(days=364),
    )
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.get(code="75")
    Visit.objects.create(edition=edition_b, origin=paris, enregistre_par=user)

    figures = get_key_figures(edition_a)

    assert figures["total_visiteurs"] == 0


@pytest.mark.django_db
def test_get_ranking_orders_by_visit_count_descending():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.get(code="75")
    rhone = Origin.objects.get(code="69")

    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)

    ranking = get_ranking(edition)

    assert ranking[0]["origin__code"] == "75"
    assert ranking[0]["nombre"] == 2
    assert ranking[1]["origin__code"] == "69"
    assert ranking[1]["nombre"] == 1


@pytest.mark.django_db
def test_get_hourly_evolution_groups_visits_by_hour():
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="2026", date_debut=today, date_fin=today)
    user = User.objects.create_user(username="alice", password="pass12345")
    paris = Origin.objects.get(code="75")

    visit1 = Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    visit2 = Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.filter(id=visit1.id).update(horodatage=timezone.make_aware(datetime.datetime(2026, 6, 20, 10, 15)))
    Visit.objects.filter(id=visit2.id).update(horodatage=timezone.make_aware(datetime.datetime(2026, 6, 20, 10, 45)))

    evolution = get_hourly_evolution(edition)

    assert len(evolution) == 1
    assert evolution[0]["nombre"] == 2
