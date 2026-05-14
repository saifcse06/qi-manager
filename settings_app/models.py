from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class CompanySettings(models.Model):
    """Company information and branding settings."""
    company_name = models.CharField(max_length=255, default='QI Manager')
    company_logo = models.ImageField(upload_to='settings/company/', blank=True, null=True)
    address = models.TextField(blank=True, default='')
    contact_number = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    currency = models.CharField(max_length=10, default='USD', help_text='Currency code (e.g., USD, EUR, GBP)')
    currency_symbol = models.CharField(max_length=5, default='$', help_text='Currency symbol (e.g., $, €, £)')
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text='Timezone (e.g., UTC, America/New_York, Europe/London)'
    )
    date_format = models.CharField(
        max_length=20,
        default='Y-m-d',
        help_text='Date format (e.g., Y-m-d, d/m/Y, m/d/Y)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # Ensure only one CompanySettings instance exists
        if not self.pk and CompanySettings.objects.exists():
            self.pk = CompanySettings.objects.first().pk
        super().save(*args, **kwargs)


class EmailConfiguration(models.Model):
    """SMTP email configuration settings."""
    smtp_host = models.CharField(max_length=255, default='smtp.gmail.com', help_text='SMTP server host')
    smtp_port = models.IntegerField(default=587, help_text='SMTP server port (e.g., 587 for TLS)')
    smtp_username = models.EmailField(default='', help_text='SMTP login username (email address)')
    smtp_password = models.CharField(max_length=500, default='', blank=True, help_text='SMTP login password or app password')
    encryption_type = models.CharField(
        max_length=10,
        choices=[
            ('TLS', 'TLS'),
            ('SSL', 'SSL'),
            ('None', 'None'),
        ],
        default='TLS',
        help_text='Connection encryption type'
    )
    default_sender_name = models.CharField(max_length=255, default='', blank=True, help_text='Default sender display name')
    use_tls = models.BooleanField(default=True, help_text='Use TLS for email connection')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email Configuration'
        verbose_name_plural = 'Email Configuration'

    def __str__(self):
        return f"Email Configuration ({self.smtp_host}:{self.smtp_port})"

    def save(self, *args, **kwargs):
        # Ensure only one EmailConfiguration instance exists
        if not self.pk and EmailConfiguration.objects.exists():
            self.pk = EmailConfiguration.objects.first().pk
        super().save(*args, **kwargs)


class EmailTemplate(models.Model):
    """Email templates for various system notifications."""
    TEMPLATE_TYPES = (
        ('quotation', 'Quotation Email'),
        ('invoice', 'Invoice Email'),
        ('payment_receipt', 'Payment Receipt Email'),
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset Email'),
        ('reminder', 'Reminder Email'),
    )

    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True, help_text='Type of email template')
    subject = models.CharField(max_length=255, help_text='Email subject line')
    body = models.TextField(help_text='Email body content. Use template variables below.')
    template_variables = models.JSONField(
        default=dict,
        blank=True,
        help_text='Available variables: client_name, invoice_number, quotation_number, due_amount, company_name, signature'
    )
    is_active = models.BooleanField(default=True, help_text='Whether this template is active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['template_type']

    def __str__(self):
        return self.get_template_type_display()


class QuotationConfiguration(models.Model):
    """Quotation number format and footer settings."""
    number_format = models.CharField(
        max_length=100,
        default='Q-{YYYY}-{序号}',
        help_text='Quotation number format. Use {YYYY} for year, {MM} for month, {DD} for day, {序号} for sequential number. Example: Q-{YYYY}-{序号}'
    )
    footer_left_content = models.TextField(blank=True, default='', help_text='Content displayed on the left side of quotation footer')
    footer_right_content = models.TextField(blank=True, default='', help_text='Content displayed on the right side of quotation footer')
    terms_and_conditions = models.TextField(
        blank=True,
        default='',
        help_text='Common terms and conditions to include on quotations'
    )
    default_warranty = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Default warranty text for quotations'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Default tax rate percentage (e.g., 10.00 for 10%)'
    )
    tax_name = models.CharField(
        max_length=100,
        default='VAT',
        help_text='Name of the tax (e.g., VAT, GST, Sales Tax)'
    )
    include_tax_in_total = models.BooleanField(
        default=True,
        help_text='Whether to include tax in total amount calculation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quotation Configuration'
        verbose_name_plural = 'Quotation Configuration'

    def __str__(self):
        return f"Quotation Config ({self.number_format})"

    def save(self, *args, **kwargs):
        if not self.pk and QuotationConfiguration.objects.exists():
            self.pk = QuotationConfiguration.objects.first().pk
        super().save(*args, **kwargs)


class InvoiceConfiguration(models.Model):
    """Invoice number format and display settings."""
    number_format = models.CharField(
        max_length=100,
        default='INV-{YYYY}-{序号}',
        help_text='Invoice number format. Use {YYYY} for year, {MM} for month, {DD} for day, {序号} for sequential number. Example: INV-{YYYY}-{序号}'
    )
    seal_upload = models.ImageField(upload_to='settings/invoices/', blank=True, null=True, help_text='Company seal/logo to appear on invoices')
    signature_upload = models.ImageField(upload_to='settings/invoices/', blank=True, null=True, help_text='Authorized signature image')
    footer_text = models.TextField(blank=True, default='', help_text='Footer text to display on all invoices')
    payment_instructions = models.TextField(blank=True, default='', help_text='Payment instructions shown on invoice')
    due_days = models.PositiveIntegerField(default=30, help_text='Default payment due in days')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Invoice Configuration'
        verbose_name_plural = 'Invoice Configuration'

    def __str__(self):
        return f"Invoice Config ({self.number_format})"

    def save(self, *args, **kwargs):
        if not self.pk and InvoiceConfiguration.objects.exists():
            self.pk = InvoiceConfiguration.objects.first().pk
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    """Available payment methods for the system."""
    PAYMENT_TYPE_CHOICES = (
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100, help_text='Payment method display name')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, help_text='Type of payment method')
    description = models.TextField(blank=True, default='', help_text='Brief description of the payment method')
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text='Payment method specific details (e.g., bank name, account number - stored encrypted in production)'
    )
    is_active = models.BooleanField(default=True, help_text='Whether this payment method is currently active')
    is_default = models.BooleanField(default=False, help_text='Whether this is the default payment method')
    sort_order = models.PositiveIntegerField(default=0, help_text='Display order')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class PaymentTerm(models.Model):
    """Payment terms definitions."""
    name = models.CharField(max_length=100, help_text='Payment term name (e.g., Net 30, Due on Receipt)')
    days = models.PositiveIntegerField(default=0, help_text='Number of days for payment')
    description = models.TextField(blank=True, default='', help_text='Description of the payment term')
    is_active = models.BooleanField(default=True, help_text='Whether this payment term is active')
    is_default = models.BooleanField(default=False, help_text='Whether this is the default payment term')
    sort_order = models.PositiveIntegerField(default=0, help_text='Display order')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Term'
        verbose_name_plural = 'Payment Terms'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.days} days)"