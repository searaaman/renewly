from django.core.validators import RegexValidator
from django.db import models


class Client(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        SUSPENDED = 'suspended', 'Suspended'

    client_code = models.CharField(max_length=10, unique=True, null=True, editable=False)
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[6-9]\d{9}$', 'Enter a valid 10-digit mobile number.')],
    )
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    gstin = models.CharField(
        'GSTIN',
        max_length=15,
        blank=True,
        validators=[RegexValidator(r'^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$', 'Enter a valid 15-character GSTIN.')],
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    onboarded_on = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.client_code} · {self.company_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.client_code:
            self.client_code = f'CL-{self.pk:03d}'
            super().save(update_fields=['client_code'])