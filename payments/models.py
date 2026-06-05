from django.db import models
from django.conf import settings
from django.utils import timezone
from invoices.models import Invoice
from settings_app.models import PaymentMethod


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method_name = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_payments')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice_id'], name='idx_payment_invoice'),
            models.Index(fields=['status'], name='idx_payment_status'),
            models.Index(fields=['payment_date'], name='idx_payment_date'),
            models.Index(fields=['reference_number'], name='idx_payment_reference'),
            models.Index(fields=['is_deleted'], name='idx_payment_deleted'),
        ]

    def __str__(self):
        return f"Payment #{self.id} - Invoice {self.invoice.invoice_number} - {self.amount}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.payment_method and not self.payment_method_name:
            self.payment_method_name = self.payment_method.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        _update_invoice_paid_amount(invoice)


class PaymentRefund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_date = models.DateField(default=timezone.now)
    reference_number = models.CharField(max_length=100, blank=True)
    reason = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_payment_refunds')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_payment_refunds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Refund'
        verbose_name_plural = 'Payment Refunds'
        ordering = ['-refund_date', '-created_at']
        indexes = [
            models.Index(fields=['payment_id'], name='idx_refund_payment'),
            models.Index(fields=['refund_date'], name='idx_refund_date'),
            models.Index(fields=['is_deleted'], name='idx_refund_deleted'),
        ]

    def __str__(self):
        return f"Refund #{self.id} - Payment #{self.payment_id} - {self.amount}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def delete(self, *args, **kwargs):
        invoice = self.payment.invoice
        super().delete(*args, **kwargs)
        _update_invoice_paid_amount(invoice)


class PaymentHistory(models.Model):
    ACTION_CHOICES = [
        ('create', 'Payment Created'),
        ('update', 'Payment Updated'),
        ('delete', 'Payment Deleted'),
        ('status_change', 'Status Changed'),
        ('refund', 'Refund Issued'),
        ('refund_deleted', 'Refund Deleted'),
        ('receipt_sent', 'Receipt Sent'),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment History'
        verbose_name_plural = 'Payment Histories'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['payment_id'], name='idx_paymenthistory_payment'),
            models.Index(fields=['action'], name='idx_paymenthistory_action'),
            models.Index(fields=['timestamp'], name='idx_paymenthistory_timestamp'),
        ]

    def __str__(self):
        return f"Payment #{self.payment_id} - {self.get_action_display()}"


def _update_invoice_paid_amount(invoice):
    total_paid = sum(
        p.amount for p in invoice.payments.filter(is_deleted=False, status='completed')
    )
    invoice.paid_amount = total_paid
    invoice.update_status_from_payment()
    invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])
