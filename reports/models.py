# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.utils import timezone


class ReportTemplate(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('quotation', 'Quotation Report'),
        ('invoice', 'Invoice Report'),
        ('payment', 'Payment Report'),
        ('client', 'Client Report'),
    ]

    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='report_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class SavedReport(models.Model):
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='saved_reports')
    name = models.CharField(max_length=255)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    parameters = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to='reports/%Y/%m/%d/', blank=True, null=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='saved_reports')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saved Report'
        verbose_name_plural = 'Saved Reports'
        ordering = ['-generated_at']

    def __str__(self):
        return self.name
