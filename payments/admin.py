from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'paid_on', 'method', 'txn_ref']
    list_filter = ['method']
    search_fields = ['subscription__client__company_name', 'txn_ref']
