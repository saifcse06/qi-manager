from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportDashboardView.as_view(), name='dashboard'),
    path('sales/', views.SalesReportView.as_view(), name='sales_report'),
    path('sales/export/', views.SalesExportView.as_view(), name='sales_export'),
    path('quotation/', views.QuotationReportView.as_view(), name='quotation_report'),
    path('quotation/export/', views.QuotationExportView.as_view(), name='quotation_export'),
    path('invoice/', views.InvoiceReportView.as_view(), name='invoice_report'),
    path('invoice/export/', views.InvoiceExportView.as_view(), name='invoice_export'),
    path('payment/', views.PaymentReportView.as_view(), name='payment_report'),
    path('payment/export/', views.PaymentExportView.as_view(), name='payment_export'),
    path('client/', views.ClientReportView.as_view(), name='client_report'),
    path('client/export/', views.ClientExportView.as_view(), name='client_export'),
]
