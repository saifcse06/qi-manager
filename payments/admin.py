from django.contrib import admin
from .models import Payment, PaymentRefund, PaymentHistory


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'payment_method_name', 'payment_date', 'reference_number', 'status', 'created_at']
    list_filter = ['status', 'payment_date', 'is_deleted', 'created_at']
    search_fields = ['id', 'invoice__invoice_number', 'reference_number', 'payment_method_name', 'invoice__client__company_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'payment_method_name']
    actions = ['mark_completed', 'mark_failed', 'mark_cancelled']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)

    @admin.action(description='Mark selected payments as Completed')
    def mark_completed(self, request, queryset):
        for payment in queryset:
            payment.status = 'completed'
            payment.save()

    @admin.action(description='Mark selected payments as Failed')
    def mark_failed(self, request, queryset):
        for payment in queryset:
            payment.status = 'failed'
            payment.save()

    @admin.action(description='Mark selected payments as Cancelled')
    def mark_cancelled(self, request, queryset):
        for payment in queryset:
            payment.status = 'cancelled'
            payment.save()


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'amount', 'refund_date', 'reference_number', 'created_at']
    list_filter = ['refund_date', 'is_deleted', 'created_at']
    search_fields = ['id', 'payment__id', 'reference_number', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)

    def has_add_permission(self, request):
        return False


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['payment', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['payment__id', 'description']
    readonly_fields = ['payment', 'action', 'performed_by', 'description', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
