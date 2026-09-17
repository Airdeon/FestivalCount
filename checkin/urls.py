from django.contrib.auth import views as auth_views
from django.urls import path

from checkin import views

app_name = "checkin"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("inscription/", views.signup, name="signup"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("festivals/creer/", views.festival_create, name="festival_create"),
    path("festivals/rejoindre/", views.festival_search, name="festival_search"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
    path("f/<slug:festival_slug>/enregistrement/visites/", views.visit_create, name="visit_create"),
    path(
        "f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/",
        views.visit_cancel,
        name="visit_cancel",
    ),
    path("f/<slug:festival_slug>/rejoindre/", views.membership_request_create, name="membership_request_create"),
    path("f/<slug:festival_slug>/stats/", views.stats, name="stats"),
    path("f/<slug:festival_slug>/stats/data/", views.stats_data, name="stats_data"),
    path("f/<slug:festival_slug>/editions/", views.edition_list, name="edition_list"),
    path("f/<slug:festival_slug>/benevoles/", views.volunteer_list, name="volunteer_list"),
    path(
        "f/<slug:festival_slug>/benevoles/demandes/<int:request_id>/accepter/",
        views.membership_request_accept,
        name="membership_request_accept",
    ),
    path(
        "f/<slug:festival_slug>/benevoles/demandes/<int:request_id>/refuser/",
        views.membership_request_reject,
        name="membership_request_reject",
    ),
    path(
        "f/<slug:festival_slug>/benevoles/<int:membership_id>/retirer/",
        views.volunteer_remove,
        name="volunteer_remove",
    ),
]
