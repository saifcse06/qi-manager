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
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'date_format': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['timezone'].choices = [
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
        ]
        self.fields['date_format'].choices = [
            ('Y-m-d', 'YYYY-MM-DD (2026-05-11)'),
            ('d/m/Y', 'DD/MM/YYYY (11/05/2026)'),
            ('m/d/Y', 'MM/DD/YYYY (05/11/2026)'),
            ('d M Y', 'DD Mon YYYY (11 May 2026)'),
            ('M d, Y', 'Mon DD, YYYY (May 11, 2026)'),
        ]


class EmailConfigurationForm(forms.ModelForm):
    class Meta:
        model = EmailConfiguration
        fields = (
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'encryption_type', 'use_tls', 'default_sender_name'
        )
        widgets = {
            'smtp_host': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'smtp_username': forms.EmailInput(attrs={'class': 'form-control'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'encryption_type': forms.Select(attrs={'class': 'form-select'}),
            'use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_sender_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['encryption_type'].choices = [
            ('TLS', 'TLS'),
            ('SSL', 'SSL'),
            ('None', 'None'),
        ]


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ('template_type', 'subject', 'body', 'template_variables', 'is_active')
        widgets = {
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'template_variables': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"client_name": "John Doe", "invoice_number": "INV-001", ...}'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuotationConfigurationForm(forms.ModelForm):
    class Meta:
        model = QuotationConfiguration
        fields = (
            'number_format', 'footer_left_content', 'footer_right_content',
            'terms_and_conditions', 'default_warranty', 'tax_name', 'tax_rate', 'include_tax_in_total'
        )
        widgets = {
            'number_format': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Q-{YYYY}-{序号}'}),
            'footer_left_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Left footer content'}),
            'footer_right_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Right footer content'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'default_warranty': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'include_tax_in_total': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvoiceConfigurationForm(forms.ModelForm):
    class Meta:
        model = InvoiceConfiguration
        fields = (
            'number_format', 'seal_upload', 'signature_upload',
            'footer_text', 'payment_instructions', 'due_days'
        )
        widgets = {
            'number_format': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INV-{YYYY}-{序号}'}),
            'seal_upload': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature_upload': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'due_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ('name', 'payment_type', 'description', 'details', 'is_active', 'is_default', 'sort_order')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"bank_name": "...", "account_number": "..."}'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_type'].choices = [
            ('bank_transfer', 'Bank Transfer'),
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('paypal', 'PayPal'),
            ('stripe', 'Stripe'),
            ('other', 'Other'),
        ]


class PaymentTermForm(forms.ModelForm):
    class Meta:
        model = PaymentTerm
        fields = ('name', 'days', 'description', 'is_active', 'is_default', 'sort_order')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'days': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }