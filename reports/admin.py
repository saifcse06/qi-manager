from django.contrib import admin
from .models import ReportTemplate, SavedReport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name']


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'export_format', 'generated_by', 'generated_at']
    list_filter = ['export_format', 'generated_at']
    search_fields = ['name']
    readonly_fields = ['generated_at']

    def has_add_permission(self, request):
        return False
