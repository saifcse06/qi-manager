from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Invoice URLs
    path('', views.InvoiceListView.as_view(), name='invoice_list'),
    path('create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    
    # Invoice Item URLs
    path('<int:invoice_pk>/items/add/', views.InvoiceItemCreateView.as_view(), name='invoiceitem_create'),
    path('items/<int:pk>/update/', views.InvoiceItemUpdateView.as_view(), name='invoiceitem_update'),
    path('items/<int:pk>/delete/', views.InvoiceItemDeleteView.as_view(), name='invoiceitem_delete'),
    
    # PDF and Email URLs
    path('<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('<int:pk>/email/', views.InvoiceEmailView.as_view(), name='invoice_email'),
    path('<int:pk>/reminder/', views.InvoiceReminderEmailView.as_view(), name='invoice_reminder'),
    
    # History URLs
    path('<int:pk>/history/', views.InvoiceHistoryView.as_view(), name='invoice_history'),
    
    # Convert from Quotation
    path('convert-from-quotation/<int:quotation_pk>/', views.InvoiceConvertView.as_view(), name='invoice_convert'),
]