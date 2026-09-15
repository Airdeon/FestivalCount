from django.db import models


class Festival(models.Model):
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom
