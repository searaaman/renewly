from django.contrib import admin

from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_code', 'company_name', 'contact_person', 'city', 'status']
    list_filter = ['status']
    search_fields = ['company_name', 'client_code']