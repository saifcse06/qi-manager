from django.db import models
from django.conf import settings
from django.utils import timezone
from clients.models import Client, ClientContactPerson
from quotations.models import Quotation


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('unpaid', 'Unpaid'),
        ('partial_paid', 'Partial Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, blank=True, null=True, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    contact_person = models.ForeignKey(ClientContactPerson, on_delete=models.SET_NULL, blank=True, null=True, related_name='invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_invoices')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number'], name='idx_invoice_number'),
            models.Index(fields=['client_id'], name='idx_invoice_client'),
            models.Index(fields=['status'], name='idx_invoice_status'),
            models.Index(fields=['is_deleted'], name='idx_invoice_deleted'),
            models.Index(fields=['quotation_id'], name='idx_invoice_quotation'),
        ]
    
    def __str__(self):
        return self.invoice_number
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_amount(self):
        return self.subtotal - self.discount_amount + self.tax_amount
    
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    def update_status_from_payment(self):
        """Auto-update status based on payment amount."""
        if self.paid_amount <= 0:
            self.status = 'unpaid'
        elif self.paid_amount >= self.total_amount:
            self.status = 'paid'
        else:
            self.status = 'partial_paid'
        self.save(update_fields=['status', 'updated_at'])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['invoice_id'], name='idx_invoiceitem_invoice'),
            models.Index(fields=['product_id'], name='idx_invoiceitem_product'),
        ]
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def discounted_price(self):
        return self.unit_price * (1 - self.discount_percentage / 100)
    
    @property
    def tax_amount(self):
        return self.discounted_price * self.quantity * (self.tax_percentage / 100)
    
    @property
    def total_price(self):
        return (self.discounted_price * self.quantity) + self.tax_amount


class InvoiceHistory(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('email_sent', 'Email Sent'),
        ('status_change', 'Status Changed'),
        ('payment_received', 'Payment Received'),
        ('converted_from_quotation', 'Converted from Quotation'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Invoice History'
        verbose_name_plural = 'Invoice Histories'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['invoice_id'], name='idx_invoicehistory_invoice'),
            models.Index(fields=['action'], name='idx_invoicehistory_action'),
            models.Index(fields=['timestamp'], name='idx_invoicehistory_timestamp'),
        ]
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.get_action_display()}"