from django.contrib import admin

from checkin.models import Edition, Festival


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ["nom", "slug"]
    prepopulated_fields = {"slug": ["nom"]}


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["nom", "festival", "date_debut", "date_fin", "est_active"]
    list_filter = ["festival"]
