from django.contrib import admin
from .models import Client, ClientContactPerson


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'email', 'phone', 'status', 'is_deleted', 'created_at']
    list_filter = ['status', 'is_deleted', 'created_at']
    search_fields = ['company_name', 'company_registration_no', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']


@admin.register(ClientContactPerson)
class ClientContactPersonAdmin(admin.ModelAdmin):
    list_display = ['person_name', 'client', 'designation', 'email', 'status', 'is_primary', 'is_deleted', 'created_at']
    list_filter = ['status', 'is_primary', 'is_deleted', 'created_at']
    search_fields = ['person_name', 'designation', 'department', 'mobile_number', 'email']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']