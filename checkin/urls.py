from django.contrib.auth import views as auth_views
from django.urls import path

from checkin import views

app_name = "checkin"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("festivals/", views.select_festival, name="select_festival"),
    path("f/<slug:festival_slug>/enregistrement/", views.register, name="register"),
    path("f/<slug:festival_slug>/enregistrement/visites/", views.visit_create, name="visit_create"),
    path(
        "f/<slug:festival_slug>/enregistrement/visites/<int:visit_id>/annuler/",
        views.visit_cancel,
        name="visit_cancel",
    ),
    path("f/<slug:festival_slug>/stats/", views.stats, name="stats"),
    path("f/<slug:festival_slug>/stats/data/", views.stats_data, name="stats_data"),
    path("f/<slug:festival_slug>/editions/", views.edition_list, name="edition_list"),
]
