from django.contrib import admin

from checkin.models import Festival


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ["nom", "slug"]
    prepopulated_fields = {"slug": ["nom"]}
