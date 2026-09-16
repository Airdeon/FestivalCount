from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from checkin.models import Membership, Origin
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
