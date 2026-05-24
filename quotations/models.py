from django.db import models
from django.conf import settings
from django.utils import timezone
from clients.models import Client, ClientContactPerson
from products.models import Product


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to Invoice'),
    ]
    
    quotation_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotations')
    contact_person = models.ForeignKey(ClientContactPerson, on_delete=models.SET_NULL, blank=True, null=True, related_name='quotations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_quotations')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Quotation'
        verbose_name_plural = 'Quotations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quotation_number'], name='idx_quotation_number'),
            models.Index(fields=['client_id'], name='idx_quotation_client'),
            models.Index(fields=['status'], name='idx_quotation_status'),
            models.Index(fields=['is_deleted'], name='idx_quotation_deleted'),
        ]
    
    def __str__(self):
        return self.quotation_number
    
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


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Quotation Item'
        verbose_name_plural = 'Quotation Items'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['quotation_id'], name='idx_quotationitem_quotation'),
            models.Index(fields=['product_id'], name='idx_quotationitem_product'),
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


class QuotationHistory(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('email_sent', 'Email Sent'),
        ('status_change', 'Status Changed'),
    ]
    
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Quotation History'
        verbose_name_plural = 'Quotation Histories'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['quotation_id'], name='idx_quotationhistory_quotation'),
            models.Index(fields=['action'], name='idx_quotationhistory_action'),
            models.Index(fields=['timestamp'], name='idx_quotationhistory_timestamp'),
        ]
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.get_action_display()}"