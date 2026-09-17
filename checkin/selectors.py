from django.utils import timezone
from django.utils.text import slugify

from checkin.models import Festival


def get_active_edition(festival):
    today = timezone.localdate()
    return festival.editions.filter(date_debut__lte=today, date_fin__gte=today).first()


def generate_unique_festival_slug(nom):
    base_slug = slugify(nom)
    slug = base_slug
    counter = 1
    while Festival.objects.filter(slug=slug).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug
