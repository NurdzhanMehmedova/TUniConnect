from django import forms
from django.utils import timezone
from internships.models import InternOffer
from companies.models import Location

class InternOfferForm(forms.ModelForm):
    location_text = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Пример: София"})
    )

    class Meta:
        model = InternOffer
        fields = [
            "title",
            "description",
            "responsibilities",
            "requirements",
            "benefits",
            "field",
            "salary_type",
            "workspace_type",
            "start_date",
            "end_date",
        ]

        widgets = {

            "title": forms.TextInput(attrs={
                "placeholder": " "
            }),

            "description": forms.Textarea(attrs={
                "placeholder": " ",
                "rows": 4
            }),

            "field": forms.Select(attrs={
                "placeholder": " "
            }),

            "salary_type": forms.Select(attrs={
                "placeholder": " "
            }),

            "workspace_type": forms.Select(attrs={
                "placeholder": " "
            }),

            "location": forms.TextInput(attrs={
                "placeholder": "Пример: София"
            }),

            "start_date": forms.DateInput(attrs={
                "type": "date"
            }),

            "end_date": forms.DateInput(attrs={
                "type": "date"
            }),

            "responsibilities": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Всяка отговорност на нов ред"
            }),

            "requirements": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Всяко изискване на нов ред"
            }),

            "benefits": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Всяко предимство на нов ред"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location_text"].required = True

        if self.instance and self.instance.pk and self.instance.location:
            self.initial["location_text"] = self.instance.location.city_name

    def clean_location_text(self):
        location_name = (self.cleaned_data.get("location_text") or "").strip()
        if not location_name:
            raise forms.ValidationError("Моля, въведете град.")
        return location_name

    def save(self, commit=True):
        offer = super().save(commit=False)
        location_name = self.cleaned_data.get("location_text")
        if location_name:
            location_obj, _ = Location.objects.get_or_create(city_name=location_name)
            offer.location = location_obj

        if commit:
            offer.save()
        return offer

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        if start_date and start_date < today:
            self.add_error("start_date", "Началната дата не може да бъде в миналото.")

        if end_date and end_date < today:
            self.add_error("end_date", "Крайната дата не може да бъде в миналото.")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "Крайната дата трябва да е след началната дата.")

        return cleaned_data