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


class Origin(models.Model):
    TYPE_DEPARTEMENT = "departement"
    TYPE_DOM_TOM = "dom_tom"
    TYPE_PAYS = "pays"
    TYPE_AUTRE = "autre"
    TYPE_CHOICES = [
        (TYPE_DEPARTEMENT, "Département"),
        (TYPE_DOM_TOM, "DOM-TOM"),
        (TYPE_PAYS, "Pays"),
        (TYPE_AUTRE, "Autre"),
    ]

    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    groupe = models.CharField(max_length=50)
    ordre_affichage = models.IntegerField()

    class Meta:
        ordering = ["ordre_affichage"]

    def __str__(self):
        return f"{self.code} — {self.nom}"


class Visit(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name="visits")
    origin = models.ForeignKey(Origin, on_delete=models.PROTECT, related_name="visits")
    precision_libre = models.CharField(max_length=100, blank=True, default="")
    horodatage = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="visits")

    class Meta:
        ordering = ["-horodatage"]

    def __str__(self):
        return f"{self.origin.nom} — {self.horodatage:%d/%m/%Y %H:%M}"
