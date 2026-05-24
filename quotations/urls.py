from django.urls import path
from . import views

app_name = 'quotations'

urlpatterns = [
    # Quotation URLs
    path('', views.QuotationListView.as_view(), name='quotation_list'),
    path('create/', views.QuotationCreateView.as_view(), name='quotation_create'),
    path('<int:pk>/', views.QuotationDetailView.as_view(), name='quotation_detail'),
    path('<int:pk>/update/', views.QuotationUpdateView.as_view(), name='quotation_update'),
    path('<int:pk>/delete/', views.QuotationDeleteView.as_view(), name='quotation_delete'),
    
    # Quotation Item URLs
    path('<int:quotation_pk>/items/add/', views.QuotationItemCreateView.as_view(), name='quotationitem_create'),
    path('items/<int:pk>/update/', views.QuotationItemUpdateView.as_view(), name='quotationitem_update'),
    path('items/<int:pk>/delete/', views.QuotationItemDeleteView.as_view(), name='quotationitem_delete'),
    
    # PDF and Email URLs
    path('<int:pk>/pdf/', views.QuotationPDFView.as_view(), name='quotation_pdf'),
    path('<int:pk>/email/', views.QuotationEmailView.as_view(), name='quotation_email'),
    
    # History URLs
    path('<int:pk>/history/', views.QuotationHistoryView.as_view(), name='quotation_history'),
]