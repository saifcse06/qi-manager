from django.contrib import admin
from .models import Quotation, QuotationItem, QuotationHistory


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    fields = ['product', 'description', 'quantity', 'unit_price', 'discount_percentage', 'tax_percentage']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_number', 'client', 'contact_person', 'status', 'subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'client']
    search_fields = ['quotation_number', 'client__company_name', 'contact_person__person_name']
    readonly_fields = ['quotation_number', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    inlines = [QuotationItemInline]
    
    fieldsets = (
        ('Quotation Information', {
            'fields': ('quotation_number', 'client', 'contact_person', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_conditions')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('quotation_number',)
        return self.readonly_fields


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'product', 'quantity', 'unit_price', 'discount_percentage', 'tax_percentage', 'total_price']
    list_filter = ['quotation__status', 'product__category']
    search_fields = ['quotation__quotation_number', 'product__name']


@admin.register(QuotationHistory)
class QuotationHistoryAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['quotation__quotation_number', 'performed_by__username']
    readonly_fields = ['quotation', 'action', 'performed_by', 'description', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False