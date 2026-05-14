from django import forms
from .models import (
    CompanySettings,
    EmailConfiguration,
    EmailTemplate,
    QuotationConfiguration,
    InvoiceConfiguration,
    PaymentMethod,
    PaymentTerm,
)


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = (
            'company_name', 'company_logo', 'address', 'contact_number',
            'email', 'website', 'currency', 'currency_symbol', 'timezone', 'date_format'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'timezone': forms.Select(choices=[
                ('UTC', 'UTC'),
                ('America/New_York', 'America/New_York (EST)'),
                ('America/Chicago', 'America/Chicago (CST)'),
                ('America/Los_Angeles', 'America/Los_Angeles (PST)'),
                ('Europe/London', 'Europe/London (GMT)'),
                ('Europe/Berlin', 'Europe/Berlin (CET)'),
                ('Europe/Paris', 'Europe/Paris (CET)'),
                ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
                ('Asia/Shanghai', 'Asia/Shanghai (CST)'),
                ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
                ('Australia/Sydney', 'Australia/Sydney (AEST)'),
            ]),
            'date_format': forms.Select(choices=[
                ('Y-m-d', 'YYYY-MM-DD (2026-05-11)'),
                ('d/m/Y', 'DD/MM/YYYY (11/05/2026)'),
                ('m/d/Y', 'MM/DD/YYYY (05/11/2026)'),
                ('d M Y', 'DD Mon YYYY (11 May 2026)'),
                ('M d, Y', 'Mon DD, YYYY (May 11, 2026)'),
            ]),
        }


class EmailConfigurationForm(forms.ModelForm):
    class Meta:
        model = EmailConfiguration
        fields = (
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'encryption_type', 'use_tls', 'default_sender_name'
        )
        widgets = {
            'smtp_password': forms.PasswordInput(),
            'encryption_type': forms.Select(choices=[
                ('TLS', 'TLS'),
                ('SSL', 'SSL'),
                ('None', 'None'),
            ]),
        }


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ('template_type', 'subject', 'body', 'template_variables', 'is_active')
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
            'template_variables': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '{"client_name": "John Doe", "invoice_number": "INV-001", ...}'
            }),
        }


class QuotationConfigurationForm(forms.ModelForm):
    class Meta:
        model = QuotationConfiguration
        fields = (
            'number_format', 'footer_left_content', 'footer_right_content',
            'terms_and_conditions', 'default_warranty', 'tax_name', 'tax_rate', 'include_tax_in_total'
        )
        widgets = {
            'number_format': forms.TextInput(attrs={'placeholder': 'Q-{YYYY}-{序号}'}),
            'footer_left_content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Left footer content'}),
            'footer_right_content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Right footer content'}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 5}),
            'default_warranty': forms.TextInput(),
        }


class InvoiceConfigurationForm(forms.ModelForm):
    class Meta:
        model = InvoiceConfiguration
        fields = (
            'number_format', 'seal_upload', 'signature_upload',
            'footer_text', 'payment_instructions', 'due_days'
        )
        widgets = {
            'number_format': forms.TextInput(attrs={'placeholder': 'INV-{YYYY}-{序号}'}),
            'footer_text': forms.Textarea(attrs={'rows': 3}),
            'payment_instructions': forms.Textarea(attrs={'rows': 4}),
        }


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ('name', 'payment_type', 'description', 'details', 'is_active', 'is_default', 'sort_order')
        widgets = {
            'payment_type': forms.Select(choices=[
                ('bank_transfer', 'Bank Transfer'),
                ('credit_card', 'Credit Card'),
                ('debit_card', 'Debit Card'),
                ('cash', 'Cash'),
                ('check', 'Check'),
                ('paypal', 'PayPal'),
                ('stripe', 'Stripe'),
                ('other', 'Other'),
            ]),
            'details': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '{"bank_name": "...", "account_number": "..."}'
            }),
        }


class PaymentTermForm(forms.ModelForm):
    class Meta:
        model = PaymentTerm
        fields = ('name', 'days', 'description', 'is_active', 'is_default', 'sort_order')