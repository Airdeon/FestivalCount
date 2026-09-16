from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from checkin.models import Festival, Membership


def membership_required(roles=None):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, festival_slug, *args, **kwargs):
            festival = get_object_or_404(Festival, slug=festival_slug)
            membership = Membership.objects.filter(user=request.user, festival=festival).first()
            if membership is None or (roles is not None and membership.role not in roles):
                messages.error(request, "Vous n'avez pas accès à cette page.")
                return redirect("checkin:select_festival")
            request.festival = festival
            request.membership = membership
            return view_func(request, festival_slug, *args, **kwargs)
        return wrapped_view
    return decorator
