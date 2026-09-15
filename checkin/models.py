from django.conf import settings
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


class Membership(models.Model):
    ROLE_ORGANISATEUR = "organisateur"
    ROLE_BENEVOLE = "benevole"
    ROLE_CHOICES = [
        (ROLE_ORGANISATEUR, "Organisateur"),
        (ROLE_BENEVOLE, "Bénévole"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "festival"], name="unique_membership_per_user_festival"),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.festival.nom} ({self.get_role_display()})"
