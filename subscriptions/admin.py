from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_user']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['client', 'plan', 'start_date', 'end_date', 'licensed_users', 'active_users', 'amount', 'status']
    list_filter = ['plan']
    search_fields = ['client__company_name']
