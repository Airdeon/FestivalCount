from django.utils import timezone


def get_active_edition(festival):
    today = timezone.localdate()
    return festival.editions.filter(date_debut__lte=today, date_fin__gte=today).first()
