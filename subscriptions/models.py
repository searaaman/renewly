from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from clients.models import Client

EXPIRING_SOON_DAYS = 30


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price_per_user = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('1'))]
    )

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRING_SOON = 'expiring_soon', 'Expiring Soon'
        EXPIRED = 'expired', 'Expired'
        PENDING = 'pending', 'Pending Activation'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    licensed_users = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    active_users = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    due_date = models.DateField()
    is_activated = models.BooleanField(default=True)
    cancelled_at = models.DateField(null=True, blank=True)
    renewed_from = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['end_date']
        constraints = [
            models.CheckConstraint(condition=Q(end_date__gt=F('start_date')), name='end_after_start'),
            models.CheckConstraint(condition=Q(active_users__lte=F('licensed_users')), name='active_within_licensed'),
        ]

    def __str__(self):
        return f'{self.client.company_name} · {self.plan}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError({'end_date': 'End date must be after the start date.'})
        if self.licensed_users and self.active_users > self.licensed_users:
            raise ValidationError({'active_users': 'Active users cannot exceed licensed users.'})

    @property
    def available_licenses(self):
        return self.licensed_users - self.active_users

    @property
    def days_left(self):
        return (self.end_date - timezone.localdate()).days

    @property
    def status(self):
        if self.cancelled_at:
            return self.Status.CANCELLED
        if not self.is_activated:
            return self.Status.PENDING
        if self.days_left < 0:
            return self.Status.EXPIRED
        if self.days_left <= EXPIRING_SOON_DAYS:
            return self.Status.EXPIRING_SOON
        return self.Status.ACTIVE
