from django.core.management.base import BaseCommand
from settings_app.models import (
    CompanySettings, EmailConfiguration, EmailTemplate,
    QuotationConfiguration, InvoiceConfiguration, PaymentMethod, PaymentTerm,
)


class Command(BaseCommand):
    help = 'Seed default system settings data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding System Settings Data...")

        # Company Settings
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
        self.stdout.write(f"  {'Created' if created else 'Exists'}: CompanySettings")

        # Email Configuration
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
        self.stdout.write(f"  {'Created' if created else 'Exists'}: EmailConfiguration")

        # Email Templates
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
            self.stdout.write(f"  {'Created' if created else 'Exists'}: EmailTemplate ({template.get_template_type_display()})")

        # Quotation Configuration
        qconfig, created = QuotationConfiguration.objects.get_or_create(
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
        self.stdout.write(f"  {'Created' if created else 'Exists'}: QuotationConfiguration")

        # Invoice Configuration
        iconfig, created = InvoiceConfiguration.objects.get_or_create(
            defaults={
                'number_format': 'INV-{YYYY}-{序号}',
                'footer_text': 'Thank you for your business!',
                'payment_instructions': 'Please make payment within the due date.',
                'due_days': 30,
            }
        )
        self.stdout.write(f"  {'Created' if created else 'Exists'}: InvoiceConfiguration")

        # Payment Methods
        methods = [
            {'name': 'Bank Transfer', 'type': 'bank_transfer', 'desc': 'Direct bank transfer', 'default': True, 'order': 1},
            {'name': 'Credit Card', 'type': 'credit_card', 'desc': 'Visa, Mastercard, etc.', 'default': False, 'order': 2},
            {'name': 'Cash', 'type': 'cash', 'desc': 'Cash payment', 'default': False, 'order': 3},
            {'name': 'PayPal', 'type': 'paypal', 'desc': 'PayPal online payment', 'default': False, 'order': 4},
        ]
        for m in methods:
            method, created = PaymentMethod.objects.get_or_create(
                name=m['name'],
                defaults={
                    'payment_type': m['type'],
                    'description': m['desc'],
                    'is_default': m['default'],
                    'sort_order': m['order'],
                    'is_active': True,
                }
            )
            self.stdout.write(f"  {'Created' if created else 'Exists'}: PaymentMethod ({method.name})")

        # Payment Terms
        terms = [
            {'name': 'Due on Receipt', 'days': 0, 'default': False, 'order': 1},
            {'name': 'Net 15', 'days': 15, 'default': False, 'order': 2},
            {'name': 'Net 30', 'days': 30, 'default': True, 'order': 3},
            {'name': 'Net 60', 'days': 60, 'default': False, 'order': 4},
            {'name': 'Net 90', 'days': 90, 'default': False, 'order': 5},
        ]
        for t in terms:
            term, created = PaymentTerm.objects.get_or_create(
                name=t['name'],
                defaults={
                    'days': t['days'],
                    'description': f'Payment due in {t["days"]} days' if t['days'] > 0 else 'Payment due immediately',
                    'is_default': t['default'],
                    'sort_order': t['order'],
                    'is_active': True,
                }
            )
            self.stdout.write(f"  {'Created' if created else 'Exists'}: PaymentTerm ({term.name})")

        self.stdout.write(self.style.SUCCESS("Settings seeding complete!"))