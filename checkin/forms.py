from django import forms

from checkin.models import Edition


class EditionForm(forms.ModelForm):
    class Meta:
        model = Edition
        fields = ["nom", "date_debut", "date_fin"]
        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}),
            "date_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
        if date_debut and date_fin and date_fin < date_debut:
            raise forms.ValidationError("La date de fin doit être postérieure ou égale à la date de début.")
        return cleaned_data
