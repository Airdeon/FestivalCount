from django.db import models
from django.utils import timezone


class Festival(models.Model):
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Edition(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name="editions")
    nom = models.CharField(max_length=200)
    date_debut = models.DateField()
    date_fin = models.DateField()

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self):
        return f"{self.festival.nom} — {self.nom}"

    @property
    def est_active(self):
        today = timezone.localdate()
        return self.date_debut <= today <= self.date_fin
