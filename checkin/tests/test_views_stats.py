import datetime

import pytest
from django.urls import reverse

from checkin.models import Edition, Festival, Membership, Origin, Visit


@pytest.mark.django_db
def test_stats_denies_access_for_benevole(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_BENEVOLE)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 302


@pytest.mark.django_db
def test_stats_shows_key_figures_for_selected_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    origin = Origin.objects.get(code="75")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    Visit.objects.create(edition=edition, origin=origin, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Paris" in content
    assert 'data-total="1"' in content


@pytest.mark.django_db
def test_stats_allows_selecting_a_past_edition(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    edition_past = Edition.objects.create(
        festival=festival, nom="Édition 2025",
        date_debut=today - datetime.timedelta(days=365),
        date_fin=today - datetime.timedelta(days=364),
    )
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(
        reverse("checkin:stats", kwargs={"festival_slug": festival.slug}),
        {"edition": edition_past.id},
    )

    assert response.status_code == 200
    assert f'value="{edition_past.id}" selected' in response.content.decode()


@pytest.mark.django_db
def test_stats_ranking_includes_percentage_relative_to_max(client, django_user_model):
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    today = datetime.date.today()
    edition = Edition.objects.create(festival=festival, nom="Édition 2026", date_debut=today, date_fin=today)
    paris = Origin.objects.get(code="75")
    rhone = Origin.objects.get(code="69")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=paris, enregistre_par=user)
    Visit.objects.create(edition=edition, origin=rhone, enregistre_par=user)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "width: 100%" in content
    assert "width: 50%" in content


@pytest.mark.django_db
def test_stats_shows_hub_links_to_editions_volunteers_and_register_even_without_editions(
    client, django_user_model
):
    # Reported bug: with no edition yet, the stats page was a dead end - no way to
    # reach Editions (to create one), Benevoles (to add a volunteer), or Enregistrement
    # (to check visitors in as an organisateur). These links must show regardless of
    # whether the festival has any edition yet.
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Aucune édition pour ce festival." in content
    assert reverse("checkin:edition_list", kwargs={"festival_slug": festival.slug}) in content
    assert reverse("checkin:volunteer_list", kwargs={"festival_slug": festival.slug}) in content
    assert reverse("checkin:register", kwargs={"festival_slug": festival.slug}) in content


@pytest.mark.django_db
def test_stats_shows_back_link_even_with_a_single_festival(client, django_user_model):
    # select_festival auto-redirects a single-membership organisateur straight back to
    # this page, so the link must carry ?all=1 to bypass that shortcut instead of looping
    # (bug reported by the user: "je rentre dans la page stat mais je ne peux plus en sortir").
    festival = Festival.objects.create(nom="Festival A", slug="festival-a")
    user = django_user_model.objects.create_user(username="alice", password="pass12345")
    Membership.objects.create(user=user, festival=festival, role=Membership.ROLE_ORGANISATEUR)
    client.login(username="alice", password="pass12345")

    response = client.get(reverse("checkin:stats", kwargs={"festival_slug": festival.slug}))

    assert response.status_code == 200
    assert reverse("checkin:select_festival") + "?all=1" in response.content.decode()
