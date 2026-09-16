import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from checkin.forms import EditionForm, VolunteerCreationForm
from checkin.models import Membership, Origin, Visit
from checkin.permissions import membership_required
from checkin.selectors import get_active_edition
from checkin.stats import get_hourly_evolution, get_key_figures, get_ranking


@login_required
def select_festival(request):
    memberships = Membership.objects.filter(user=request.user).select_related("festival")
    if memberships.count() == 1:
        membership = memberships.first()
        target_view = "checkin:stats" if membership.role == Membership.ROLE_ORGANISATEUR else "checkin:register"
        return redirect(target_view, festival_slug=membership.festival.slug)
    return render(request, "checkin/select_festival.html", {"memberships": memberships})


@membership_required()
def register(request, festival_slug):
    edition = get_active_edition(request.festival)
    origins = Origin.objects.all() if edition else Origin.objects.none()
    return render(
        request,
        "checkin/register.html",
        {"edition": edition, "origins": origins},
    )


@require_POST
@membership_required()
def visit_create(request, festival_slug):
    edition = get_active_edition(request.festival)
    if edition is None:
        return JsonResponse({"error": "Aucune édition en cours."}, status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Requête invalide."}, status=400)

    origin_code = payload.get("origin_code")
    origin = Origin.objects.filter(code=origin_code).first()
    if origin is None:
        return JsonResponse({"error": "Origine inconnue."}, status=400)

    precision_libre = payload.get("precision_libre") or ""

    visit = Visit.objects.create(
        edition=edition,
        origin=origin,
        enregistre_par=request.user,
        precision_libre=precision_libre,
    )

    return JsonResponse({"id": visit.id, "origin_nom": origin.nom}, status=201)


@require_POST
@membership_required()
def visit_cancel(request, festival_slug, visit_id):
    visit = Visit.objects.filter(id=visit_id, edition__festival=request.festival).first()
    if visit is None:
        return JsonResponse({"error": "Visite introuvable."}, status=404)
    visit.delete()
    return JsonResponse({"deleted": True})


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def stats(request, festival_slug):
    editions = request.festival.editions.all()
    active_edition = get_active_edition(request.festival)

    edition_id = request.GET.get("edition")
    edition = editions.filter(id=edition_id).first() if edition_id else active_edition
    if edition is None:
        edition = editions.first()

    context = {"editions": editions, "selected_edition": edition}
    if edition is not None:
        context["key_figures"] = get_key_figures(edition)
        context["ranking"] = get_ranking(edition)
        context["hourly_evolution"] = get_hourly_evolution(edition)
        context["is_current_edition"] = edition == active_edition

    return render(request, "checkin/stats.html", context)


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def stats_data(request, festival_slug):
    edition_id = request.GET.get("edition")
    edition = request.festival.editions.filter(id=edition_id).first()
    if edition is None:
        return JsonResponse({"error": "Édition introuvable."}, status=404)

    return JsonResponse({
        "key_figures": get_key_figures(edition),
        "ranking": get_ranking(edition),
        "hourly_evolution": get_hourly_evolution(edition),
    })


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def edition_list(request, festival_slug):
    editions = request.festival.editions.all()

    if request.method == "POST":
        form = EditionForm(request.POST)
        if form.is_valid():
            edition = form.save(commit=False)
            edition.festival = request.festival
            edition.save()
            messages.success(request, "Édition créée avec succès.")
            return redirect("checkin:edition_list", festival_slug=festival_slug)
    else:
        form = EditionForm()

    return render(request, "checkin/edition_list.html", {"editions": editions, "form": form})


@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def volunteer_list(request, festival_slug):
    memberships = Membership.objects.filter(
        festival=request.festival, role=Membership.ROLE_BENEVOLE
    ).select_related("user")

    if request.method == "POST":
        form = VolunteerCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            Membership.objects.create(user=user, festival=request.festival, role=Membership.ROLE_BENEVOLE)
            messages.success(request, "Compte bénévole créé avec succès.")
            return redirect("checkin:volunteer_list", festival_slug=festival_slug)
    else:
        form = VolunteerCreationForm()

    return render(request, "checkin/volunteer_list.html", {"memberships": memberships, "form": form})


@require_POST
@membership_required(roles=[Membership.ROLE_ORGANISATEUR])
def volunteer_remove(request, festival_slug, membership_id):
    membership = Membership.objects.filter(
        id=membership_id, festival=request.festival, role=Membership.ROLE_BENEVOLE
    ).first()
    if membership is not None:
        membership.delete()
        messages.success(request, "Accès du bénévole retiré.")
    return redirect("checkin:volunteer_list", festival_slug=festival_slug)
