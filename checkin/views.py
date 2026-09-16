from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from checkin.models import Membership


@login_required
def select_festival(request):
    memberships = Membership.objects.filter(user=request.user).select_related("festival")
    return render(request, "checkin/select_festival.html", {"memberships": memberships})
