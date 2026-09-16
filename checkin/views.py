import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from checkin.models import Membership, Origin, Visit
from checkin.permissions import membership_required
from checkin.selectors import get_active_edition


@login_required
def select_festival(request):
    memberships = Membership.objects.filter(user=request.user).select_related("festival")
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
