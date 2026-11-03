from django import forms
from django.utils import timezone

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'company_name', 'contact_person', 'email', 'phone', 'city',
            'address', 'gstin', 'status', 'onboarded_on', 'notes',
        ]
        widgets = {
            'onboarded_on': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            field.widget.attrs['class'] = 'form-select' if is_select else 'form-control'

    def clean_onboarded_on(self):
        date = self.cleaned_data['onboarded_on']
        if date > timezone.localdate():
            raise forms.ValidationError('Onboarding date cannot be in the future.')
        return date