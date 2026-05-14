#!/usr/bin/env python
"""
Seed script to populate default system settings.
Run with: DJANGO_SETTINGS_MODULE=config.settings venv/bin/python seed_settings_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/mdsaifuddin/Desktop/SaifDev/QI-Management/Development/qi-manager')
django.setup()

from settings_app.models import (
    CompanySettings, EmailConfiguration, EmailTemplate,
    QuotationConfiguration, InvoiceConfiguration, PaymentMethod, PaymentTerm,
)


def seed_company_settings():
    """Create default company settings."""
    company, created = CompanySettings.objects.get_or_create(
        defaults={
            'company_name': 'QI Manager',
            'address': '123 Main Street, New York, NY 10001',
            'contact_number': '+1 234 567 8900',
            'email': 'info@example.com',
            'website': 'https://example.com',
            'currency': 'USD',
            'currency_symbol': '$',
            'timezone': 'UTC',
            'date_format': 'Y-m-d',
        }
    )
    status = "Created" if created else "Already exists"
    print(f"  [{status}] CompanySettings: {company.company_name}")


def seed_email_configuration():
    """Create default email configuration."""
    config, created = EmailConfiguration.objects.get_or_create(
        defaults={
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': '',
            'smtp_password': '',
            'encryption_type': 'TLS',
            'use_tls': True,
            'default_sender_name': 'QI Manager',
        }
    )
    status = "Created" if created else "Already exists"
    print(f"  [{status}] EmailConfiguration: {config.smtp_host}:{config.smtp_port}")


def seed_email_templates():
    """Create default email templates."""
    templates = [
        {
            'template_type': 'quotation',
            'subject': 'Quotation #{quotation_number} from {company_name}',
            'body': (
                'Dear {client_name},\n\n'
                'Thank you for your inquiry. Please find your quotation details below:\n\n'
                'Quotation Number: {quotation_number}\n'
                'Due Amount: {due_amount}\n'
                'Due Date: {due_date}\n\n'
                'If you have any questions, please do not hesitate to contact us.\n\n'
                'Best regards,\n{company_name}\n\n{signature}'
            ),
            'template_variables': {
                'client_name': 'Client Name',
                'quotation_number': 'Quotation Number',
                'due_amount': 'Due Amount',
                'due_date': 'Due Date',
                'company_name': 'Company Name',
                'signature': 'Company Signature',
            },
        },
        {
            'template_type': 'invoice',
            'subject': 'Invoice #{invoice_number} from {company_name}',
            'body': (
                'Dear {client_name},\n\n'
                'Please find your invoice details below:\n\n'
                'Invoice Number: {invoice_number}\n'
                'Amount Due: {due_amount}\n'
                'Due Date: {due_date}\n\n'
                'Please make payment at your earliest convenience.\n\n'
                'Best regards,\n{company_name}\n\n{signature}'
            ),
            'template_variables': {
                'client_name': 'Client Name',
                'invoice_number': 'Invoice Number',
                'due_amount': 'Due Amount',
                'due_date': 'Due Date',
                'company_name': 'Company Name',
                'signature': 'Company Signature',
            },
        },
        {
            'template_type': 'payment_receipt',
            'subject': 'Payment Receipt #{invoice_number} from {company_name}',
            'body': (
                'Dear {client_name},\n\n'
                'This is to confirm that we have received your payment.\n\n'
                'Invoice Number: {invoice_number}\n'
                'Amount Paid: {amount}\n'
                'Payment Date: {due_date}\n\n'
                'Thank you for your business!\n\n'
                'Best regards,\n{company_name}\n\n{signature}'
            ),
            'template_variables': {
                'client_name': 'Client Name',
                'invoice_number': 'Invoice Number',
                'amount': 'Paid Amount',
                'due_date': 'Payment Date',
                'company_name': 'Company Name',
                'signature': 'Company Signature',
            },
        },
    ]

    for t in templates:
        template, created = EmailTemplate.objects.get_or_create(
            template_type=t['template_type'],
            defaults={
                'subject': t['subject'],
                'body': t['body'],
                'template_variables': t['template_variables'],
                'is_active': True,
            }
        )
        status = "Created" if created else "Already exists"
        print(f"  [{status}] EmailTemplate: {template.get_template_type_display()}")


def seed_quotation_configuration():
    """Create default quotation configuration."""
    config, created = QuotationConfiguration.objects.get_or_create(
        defaults={
            'number_format': 'Q-{YYYY}-{序号}',
            'footer_left_content': 'Thank you for your business!',
            'footer_right_content': 'Valid for 30 days',
            'terms_and_conditions': 'Payment is due upon receipt. Late payments may incur fees.',
            'default_warranty': '12 months standard warranty',
            'tax_name': 'VAT',
            'tax_rate': 10.00,
            'include_tax_in_total': True,
        }
    )
    status = "Created" if created else "Already exists"
    print(f"  [{status}] QuotationConfiguration: {config.number_format}")


def seed_invoice_configuration():
    """Create default invoice configuration."""
    config, created = InvoiceConfiguration.objects.get_or_create(
        defaults={
            'number_format': 'INV-{YYYY}-{序号}',
            'footer_text': 'Thank you for your business!',
            'payment_instructions': 'Please make payment within the due date.',
            'due_days': 30,
        }
    )
    status = "Created" if created else "Already exists"
    print(f"  [{status}] InvoiceConfiguration: {config.number_format}")


def seed_payment_methods():
    """Create default payment methods."""
    methods = [
        {'name': 'Bank Transfer', 'payment_type': 'bank_transfer', 'description': 'Direct bank transfer', 'is_default': True, 'sort_order': 1},
        {'name': 'Credit Card', 'payment_type': 'credit_card', 'description': 'Visa, Mastercard, etc.', 'is_default': False, 'sort_order': 2},
        {'name': 'Cash', 'payment_type': 'cash', 'description': 'Cash payment', 'is_default': False, 'sort_order': 3},
        {'name': 'PayPal', 'payment_type': 'paypal', 'description': 'PayPal online payment', 'is_default': False, 'sort_order': 4},
    ]

    for m in methods:
        method, created = PaymentMethod.objects.get_or_create(
            name=m['name'],
            defaults={
                'payment_type': m['payment_type'],
                'description': m['description'],
                'is_default': m['is_default'],
                'sort_order': m['sort_order'],
                'is_active': True,
            }
        )
        status = "Created" if created else "Already exists"
        print(f"  [{status}] PaymentMethod: {method.name}")


def seed_payment_terms():
    """Create default payment terms."""
    terms = [
        {'name': 'Due on Receipt', 'days': 0, 'description': 'Payment due immediately', 'is_default': False, 'sort_order': 1},
        {'name': 'Net 15', 'days': 15, 'description': 'Payment due in 15 days', 'is_default': False, 'sort_order': 2},
        {'name': 'Net 30', 'days': 30, 'description': 'Payment due in 30 days', 'is_default': True, 'sort_order': 3},
        {'name': 'Net 60', 'days': 60, 'description': 'Payment due in 60 days', 'is_default': False, 'sort_order': 4},
        {'name': 'Net 90', 'days': 90, 'description': 'Payment due in 90 days', 'is_default': False, 'sort_order': 5},
    ]

    for t in terms:
        term, created = PaymentTerm.objects.get_or_create(
            name=t['name'],
            defaults={
                'days': t['days'],
                'description': t['description'],
                'is_default': t['is_default'],
                'sort_order': t['sort_order'],
                'is_active': True,
            }
        )
        status = "Created" if created else "Already exists"
        print(f"  [{status}] PaymentTerm: {term.name} ({term.days} days)")


def main():
    print("=" * 50)
    print("Seeding System Settings Data")
    print("=" * 50)

    print("\n[1/7] Company Settings...")
    seed_company_settings()

    print("\n[2/7] Email Configuration...")
    seed_email_configuration()

    print("\n[3/7] Email Templates...")
    seed_email_templates()

    print("\n[4/7] Quotation Configuration...")
    seed_quotation_configuration()

    print("\n[5/7] Invoice Configuration...")
    seed_invoice_configuration()

    print("\n[6/7] Payment Methods...")
    seed_payment_methods()

    print("\n[7/7] Payment Terms...")
    seed_payment_terms()

    print("\n" + "=" * 50)
    print("Settings seed data complete!")
    print("=" * 50)

    # Summary
    from settings_app.models import CompanySettings, EmailTemplate, PaymentMethod, PaymentTerm
    print(f"\nSummary:")
    print(f"  Company Settings: {CompanySettings.objects.count()}")
    print(f"  Email Configs: {EmailTemplate.objects.count()}")
    print(f"  Email Templates: {EmailTemplate.objects.count()}")
    print(f"  Payment Methods: {PaymentMethod.objects.count()}")
    print(f"  Payment Terms: {PaymentTerm.objects.count()}")


if __name__ == '__main__':
    main()