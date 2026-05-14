import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, '/Users/mdsaifuddin/Desktop/SaifDev/QI-Management/Development/qi-manager')

import django
django.setup()

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

from settings_app.models import (
    CompanySettings, EmailConfiguration, EmailTemplate,
    QuotationConfiguration, InvoiceConfiguration, PaymentMethod, PaymentTerm,
)


# Override static storage for tests to avoid manifest issues
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SettingsViewTests(TestCase):
    """Test cases for the System Settings module."""

    @classmethod
    def setUpTestData(cls):
        # Create test users with different roles
        cls.super_admin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123',
            first_name='Super',
            last_name='Admin',
            is_active=True,
        )
        cls.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_active=True,
            is_staff=True,
        )
        cls.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123',
            first_name='Regular',
            last_name='User',
            is_active=True,
        )

    def setUp(self):
        self.client = Client()
        # Run seed data for each test to populate the test DB
        call_command('seed_settings', verbosity=0)

    # --- Access Tests ---

    def test_settings_page_requires_login(self):
        """Settings dashboard should redirect to login for unauthenticated users."""
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_settings_page_accessible_by_super_admin(self):
        """Super admin should be able to access settings page."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'settings_app/settings_dashboard.html')

    def test_settings_page_blocked_for_admin_via_middleware(self):
        """Admin users should be blocked by middleware (requires Super Admin)."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/settings/')
        # Middleware redirects to home since /settings/ requires Super Admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home/', response.url)

    def test_settings_page_blocked_for_regular_user(self):
        """Regular users without Super Admin role should be blocked by middleware."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home/', response.url)

    # --- Form Rendering Tests ---

    def test_company_settings_form_renders(self):
        """Company settings form should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=company')
        self.assertContains(response, 'Company Settings')
        self.assertContains(response, 'id_company_name')
        self.assertContains(response, 'id_currency')
        self.assertContains(response, 'id_timezone')

    def test_email_config_form_renders(self):
        """Email configuration form should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=email')
        self.assertContains(response, 'Email Configuration')
        self.assertContains(response, 'id_smtp_host')
        self.assertContains(response, 'id_smtp_port')
        self.assertContains(response, 'id_encryption_type')

    def test_email_template_form_renders(self):
        """Email template form should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=templates')
        self.assertContains(response, 'Email Templates')
        self.assertContains(response, 'id_template_type')
        self.assertContains(response, 'id_subject')
        self.assertContains(response, 'id_body')

    def test_quotation_config_form_renders(self):
        """Quotation configuration form should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=quotation')
        self.assertContains(response, 'Quotation Configuration')
        self.assertContains(response, 'id_number_format')
        self.assertContains(response, 'id_tax_rate')

    def test_invoice_config_form_renders(self):
        """Invoice configuration form should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=invoice')
        self.assertContains(response, 'Invoice Configuration')
        self.assertContains(response, 'id_number_format')
        self.assertContains(response, 'id_due_days')

    def test_payment_methods_renders(self):
        """Payment methods section should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=payment-method')
        self.assertContains(response, 'Payment Methods')
        self.assertContains(response, 'id_name')

    def test_payment_terms_renders(self):
        """Payment terms section should render correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/settings/?tab=payment-method')
        self.assertContains(response, 'Payment Terms')
        self.assertContains(response, 'id_days')

    # --- Form Submission Tests ---

    def test_company_settings_save(self):
        """Company settings should save correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'company',
            'company_name': 'My Test Company',
            'address': '123 Test St',
            'contact_number': '+1234567890',
            'email': 'test@mycompany.com',
            'website': 'https://mycompany.com',
            'currency': 'USD',
            'currency_symbol': '$',
            'timezone': 'UTC',
            'date_format': 'Y-m-d',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CompanySettings.objects.first().company_name, 'My Test Company')

    def test_email_config_save(self):
        """Email configuration should save correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'email',
            'smtp_host': 'smtp.custom.com',
            'smtp_port': 465,
            'smtp_username': 'custom@example.com',
            'smtp_password': 'secretpassword',
            'encryption_type': 'SSL',
            'use_tls': 'on',
            'default_sender_name': 'My Company',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        config = EmailConfiguration.objects.first()
        self.assertEqual(config.smtp_host, 'smtp.custom.com')
        self.assertEqual(config.encryption_type, 'SSL')

    def test_quotation_config_save(self):
        """Quotation configuration should save correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'quotation',
            'number_format': 'QTN-{YYYY}-{序号}',
            'footer_left_content': 'Left footer',
            'footer_right_content': 'Right footer',
            'terms_and_conditions': 'Net 30 payment terms apply.',
            'default_warranty': '24 months',
            'tax_name': 'GST',
            'tax_rate': '18.00',
            'include_tax_in_total': 'on',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        config = QuotationConfiguration.objects.first()
        self.assertEqual(config.number_format, 'QTN-{YYYY}-{序号}')
        self.assertEqual(config.tax_name, 'GST')

    def test_invoice_config_save(self):
        """Invoice configuration should save correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'invoice',
            'number_format': 'INV-{YYYY}-{序号}',
            'footer_text': 'Thank you for your business.',
            'payment_instructions': 'Wire transfer to our account.',
            'due_days': '45',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        config = InvoiceConfiguration.objects.first()
        self.assertEqual(config.due_days, 45)
        self.assertEqual(config.payment_instructions, 'Wire transfer to our account.')

    # --- Payment Method CRUD Tests ---

    def test_create_payment_method(self):
        """Payment method should create correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'payment-method',
            'name': 'Stripe',
            'payment_type': 'stripe',
            'description': 'Stripe payment gateway',
            'is_active': 'on',
            'is_default': 'on',
            'sort_order': '1',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PaymentMethod.objects.filter(name='Stripe').exists())

    def test_delete_payment_method(self):
        """Payment method should delete correctly."""
        method = PaymentMethod.objects.create(
            name='Test Method', payment_type='other', sort_order=99, is_active=True
        )
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/delete-payment-method/', {'id': method.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PaymentMethod.objects.filter(id=method.id).exists())

    # --- Payment Term CRUD Tests ---

    def test_create_payment_term(self):
        """Payment term should create correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'payment-term',
            'term_id': '',
            'name': 'Net 45',
            'days': '45',
            'description': 'Payment due in 45 days',
            'is_active': 'on',
            'is_default': '',
            'sort_order': '6',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PaymentTerm.objects.filter(name='Net 45').exists())

    def test_delete_payment_term(self):
        """Payment term should delete correctly."""
        term = PaymentTerm.objects.create(
            name='Test Term', days=7, sort_order=99, is_active=True
        )
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/delete-payment-term/', {'id': term.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PaymentTerm.objects.filter(id=term.id).exists())

    # --- Email Template Tests ---

    def test_create_email_template(self):
        """Email template should create correctly."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/settings/', {
            'active_tab': 'templates',
            'template_id': '',
            'template_type': 'welcome',
            'subject': 'Welcome to Our Platform',
            'body': 'Welcome {client_name}!',
            'is_active': 'on',
            'template_variables': '{"client_name": "User"}',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EmailTemplate.objects.filter(template_type='welcome').exists())

    # --- URL Resolution Tests ---

    def test_settings_url_resolves(self):
        """Settings URL should resolve correctly."""
        url = reverse('settings_app:settings_dashboard')
        self.assertEqual(url, '/settings/')

    def test_delete_payment_method_url_resolves(self):
        """Delete payment method URL should resolve correctly."""
        url = reverse('settings_app:delete_payment_method')
        self.assertEqual(url, '/settings/delete-payment-method/')

    # --- Defaults / Seed Data Tests ---

    def test_seed_payment_methods_exist(self):
        """Default payment methods should exist after seeding."""
        self.assertTrue(PaymentMethod.objects.filter(name='Bank Transfer').exists())
        self.assertTrue(PaymentMethod.objects.filter(name='Credit Card').exists())
        self.assertTrue(PaymentMethod.objects.filter(name='PayPal').exists())

    def test_seed_payment_terms_exist(self):
        """Default payment terms should exist after seeding."""
        self.assertTrue(PaymentTerm.objects.filter(name='Net 30').exists())
        self.assertTrue(PaymentTerm.objects.filter(name='Due on Receipt').exists())

    def test_seed_email_templates_exist(self):
        """Default email templates should exist after seeding."""
        self.assertTrue(EmailTemplate.objects.filter(template_type='quotation').exists())
        self.assertTrue(EmailTemplate.objects.filter(template_type='invoice').exists())
        self.assertTrue(EmailTemplate.objects.filter(template_type='payment_receipt').exists())

    def test_seed_company_settings_exist(self):
        """Default company settings should exist after seeding."""
        self.assertTrue(CompanySettings.objects.exists())
        self.assertEqual(CompanySettings.objects.first().company_name, 'QI Manager')

    def test_seed_invoice_config_exist(self):
        """Default invoice config should exist after seeding."""
        self.assertTrue(InvoiceConfiguration.objects.exists())
        self.assertEqual(InvoiceConfiguration.objects.first().number_format, 'INV-{YYYY}-{序号}')

    def test_seed_quotation_config_exist(self):
        """Default quotation config should exist after seeding."""
        self.assertTrue(QuotationConfiguration.objects.exists())
        self.assertEqual(QuotationConfiguration.objects.first().number_format, 'Q-{YYYY}-{序号}')