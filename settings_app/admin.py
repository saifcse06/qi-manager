from django.contrib import admin
from .models import (
    CompanySettings,
    EmailConfiguration,
    EmailTemplate,
    QuotationConfiguration,
    InvoiceConfiguration,
    PaymentMethod,
    PaymentTerm,
)


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'currency', 'timezone', 'date_format')
    search_fields = ('company_name', 'email')
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_logo', 'address', 'contact_number', 'email', 'website')
        }),
        ('Regional Settings', {
            'fields': ('currency', 'currency_symbol', 'timezone', 'date_format')
        }),
    )


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('smtp_host', 'smtp_port', 'smtp_username', 'encryption_type', 'use_tls')
    fieldsets = (
        ('SMTP Configuration', {
            'fields': ('smtp_host', 'smtp_port', 'encryption_type', 'use_tls')
        }),
        ('Authentication', {
            'fields': ('smtp_username', 'smtp_password')
        }),
        ('Sender', {
            'fields': ('default_sender_name',)
        }),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'subject', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('subject', 'body')


@admin.register(QuotationConfiguration)
class QuotationConfigurationAdmin(admin.ModelAdmin):
    list_display = ('number_format', 'tax_name', 'tax_rate', 'include_tax_in_total')
    fieldsets = (
        ('Quotation Number', {
            'fields': ('number_format',)
        }),
        ('Footer', {
            'fields': ('footer_left_content', 'footer_right_content')
        }),
        ('Terms & Conditions', {
            'fields': ('terms_and_conditions', 'default_warranty')
        }),
        ('Tax Settings', {
            'fields': ('tax_name', 'tax_rate', 'include_tax_in_total')
        }),
    )


@admin.register(InvoiceConfiguration)
class InvoiceConfigurationAdmin(admin.ModelAdmin):
    list_display = ('number_format', 'due_days')
    fieldsets = (
        ('Invoice Number', {
            'fields': ('number_format',)
        }),
        ('Branding', {
            'fields': ('seal_upload', 'signature_upload')
        }),
        ('Footer', {
            'fields': ('footer_text',)
        }),
        ('Payment', {
            'fields': ('payment_instructions', 'due_days')
        }),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'is_active', 'is_default', 'sort_order')
    list_filter = ('payment_type', 'is_active')
    list_editable = ('is_active', 'is_default', 'sort_order')


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ('name', 'days', 'is_active', 'is_default', 'sort_order')
    list_editable = ('is_active', 'is_default', 'sort_order')