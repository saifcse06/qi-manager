from django.contrib import admin
from .models import Invoice, InvoiceItem, InvoiceHistory


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'status', 'total_amount', 'paid_amount', 'balance_due', 'due_date', 'created_at']
    list_filter = ['status', 'is_deleted', 'created_at', 'due_date']
    search_fields = ['invoice_number', 'client__company_name', 'contact_person__person_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'subtotal', 'total_amount', 'balance_due']
    actions = ['mark_as_paid', 'mark_as_cancelled']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)

    @admin.action(description='Mark selected invoices as Paid')
    def mark_as_paid(self, request, queryset):
        for invoice in queryset:
            invoice.paid_amount = invoice.total_amount
            invoice.status = 'paid'
            invoice.save()
            InvoiceHistory.objects.create(
                invoice=invoice,
                action='status_change',
                performed_by=request.user,
                description=f"Status changed to Paid via admin action"
            )

    @admin.action(description='Mark selected invoices as Cancelled')
    def mark_as_cancelled(self, request, queryset):
        for invoice in queryset:
            invoice.status = 'cancelled'
            invoice.save()
            InvoiceHistory.objects.create(
                invoice=invoice,
                action='status_change',
                performed_by=request.user,
                description=f"Status changed to Cancelled via admin action"
            )


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['invoice__status', 'created_at']
    search_fields = ['invoice__invoice_number', 'product__name']


@admin.register(InvoiceHistory)
class InvoiceHistoryAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['invoice__invoice_number', 'description']
    readonly_fields = ['invoice', 'action', 'performed_by', 'description', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False