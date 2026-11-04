from django import forms

from config.forms import BootstrapModelForm

from .models import Payment


class PaymentForm(BootstrapModelForm):
    class Meta:
        model = Payment
        fields = ['subscription', 'amount', 'paid_on', 'method', 'txn_ref', 'notes']
        widgets = {
            'paid_on': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }