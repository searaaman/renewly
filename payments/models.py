from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from subscriptions.models import Subscription


class Payment(models.Model):
    class Method(models.TextChoices):
        UPI = 'upi', 'UPI'
        NEFT = 'neft', 'NEFT'
        CARD = 'card', 'Card'
        CHEQUE = 'cheque', 'Cheque'
        CASH = 'cash', 'Cash'

    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    paid_on = models.DateField()
    method = models.CharField(max_length=10, choices=Method.choices)
    txn_ref = models.CharField('Transaction / reference ID', max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-id']
        constraints = [
             models.UniqueConstraint(
                fields=['txn_ref'],
                condition=~Q(txn_ref=''),
                name='unique_txn_ref_when_present',
                violation_error_message='This transaction ID has already been recorded.',
            ),
        ]

    def __str__(self):
        return f'₹{self.amount} · {self.subscription}'

    def clean(self):
        if self.paid_on and self.paid_on > timezone.localdate():
            raise ValidationError({'paid_on': 'Payment date cannot be in the future.'})
        if self.subscription_id and self.amount:
            others = self.subscription.payments.exclude(pk=self.pk)
            remaining = self.subscription.amount - sum(p.amount for p in others)
            if self.amount > remaining:
                raise ValidationError({'amount': f'Only ₹{remaining} is outstanding on this subscription.'})

