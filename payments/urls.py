from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('<int:pk>/update/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    path('invoice/<int:invoice_pk>/', views.PaymentInvoiceListView.as_view(), name='payment_list_by_invoice'),
    path('<int:pk>/refund/', views.PaymentRefundCreateView.as_view(), name='payment_refund_create'),
    path('refunds/<int:pk>/delete/', views.PaymentRefundDeleteView.as_view(), name='payment_refund_delete'),

    path('<int:pk>/receipt/', views.PaymentReceiptView.as_view(), name='payment_receipt'),
    path('<int:pk>/receipt/pdf/', views.PaymentReceiptPDFView.as_view(), name='payment_receipt_pdf'),
    path('<int:pk>/email/', views.PaymentEmailView.as_view(), name='payment_email'),
    path('<int:pk>/history/', views.PaymentHistoryView.as_view(), name='payment_history'),
]
