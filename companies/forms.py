from django import forms
from internships.models import InternOffer


class InternOfferForm(forms.ModelForm):

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
            "location",
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

            "location": forms.Select(attrs={
                "placeholder": " "
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