from django.db import migrations

from checkin.reference_data import ORIGINS


def populate_origins(apps, schema_editor):
    Origin = apps.get_model("checkin", "Origin")
    Origin.objects.bulk_create([Origin(**data) for data in ORIGINS])


def remove_origins(apps, schema_editor):
    Origin = apps.get_model("checkin", "Origin")
    Origin.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0004_origin"),
    ]

    operations = [
        migrations.RunPython(populate_origins, remove_origins),
    ]
