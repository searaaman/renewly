from django import forms
from django.utils import timezone

from config.forms import BootstrapModelForm

from .models import Client


class ClientForm(BootstrapModelForm):
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

    def clean_onboarded_on(self):
        date = self.cleaned_data['onboarded_on']
        if date > timezone.localdate():
            raise forms.ValidationError('Onboarding date cannot be in the future.')
        return date