from django.contrib import admin

from checkin.models import Edition, Festival, Membership


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ["nom", "slug"]
    prepopulated_fields = {"slug": ["nom"]}


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["nom", "festival", "date_debut", "date_fin", "est_active"]
    list_filter = ["festival"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "festival", "role"]
    list_filter = ["festival", "role"]
