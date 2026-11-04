from django import forms

from config.forms import BootstrapModelForm

from .models import Subscription


class SubscriptionForm(BootstrapModelForm):
    class Meta:
        model = Subscription
        fields = [
            'client', 'plan', 'start_date', 'end_date', 'licensed_users',
            'active_users', 'amount', 'due_date', 'is_activated',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {'due_date': 'Payment due date', 'is_activated': 'Activated'}