from django.db import models
from django.conf import settings


class Client(models.Model):
    company_name = models.CharField(max_length=255)
    company_registration_no = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_clients')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_name'], name='idx_client_company'),
            models.Index(fields=['email'], name='idx_client_email'),
            models.Index(fields=['phone'], name='idx_client_phone'),
            models.Index(fields=['status'], name='idx_client_status'),
            models.Index(fields=['is_deleted'], name='idx_client_deleted'),
        ]

    def __str__(self):
        return self.company_name

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class ClientContactPerson(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contact_persons')
    person_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=150, blank=True, null=True)
    department = models.CharField(max_length=150, blank=True, null=True)
    mobile_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client Contact Person'
        verbose_name_plural = 'Client Contact Persons'
        ordering = ['-is_primary', 'person_name']
        indexes = [
            models.Index(fields=['client_id'], name='idx_contact_client'),
            models.Index(fields=['email'], name='idx_contact_email'),
            models.Index(fields=['mobile_number'], name='idx_contact_mobile'),
            models.Index(fields=['is_primary'], name='idx_contact_primary'),
            models.Index(fields=['is_deleted'], name='idx_contact_deleted'),
        ]

    def __str__(self):
        return f"{self.person_name} ({self.client.company_name})"

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()