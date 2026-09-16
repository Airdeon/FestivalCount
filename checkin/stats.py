from django.db.models import Count
from django.db.models.functions import TruncHour

from checkin.models import Origin, Visit


def get_key_figures(edition):
    visits = Visit.objects.filter(edition=edition)
    total = visits.count()
    nombre_departements = (
        visits.filter(origin__type__in=[Origin.TYPE_DEPARTEMENT, Origin.TYPE_DOM_TOM])
        .values("origin")
        .distinct()
        .count()
    )
    nombre_pays = (
        visits.filter(origin__type__in=[Origin.TYPE_PAYS, Origin.TYPE_AUTRE])
        .values("origin")
        .distinct()
        .count()
    )
    return {
        "total_visiteurs": total,
        "nombre_departements": nombre_departements,
        "nombre_pays": nombre_pays,
    }


def get_ranking(edition):
    return list(
        Visit.objects.filter(edition=edition)
        .values("origin__code", "origin__nom")
        .annotate(nombre=Count("id"))
        .order_by("-nombre")
    )


def get_hourly_evolution(edition):
    rows = (
        Visit.objects.filter(edition=edition)
        .annotate(heure=TruncHour("horodatage"))
        .values("heure")
        .annotate(nombre=Count("id"))
        .order_by("heure")
    )
    return [{"heure": row["heure"].isoformat(), "nombre": row["nombre"]} for row in rows]
