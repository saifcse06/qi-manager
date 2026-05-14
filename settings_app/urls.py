from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    # Main settings dashboard (tab-based)
    path('', views.SettingsDashboardView.as_view(), name='settings_dashboard'),

    # AJAX delete endpoints
    path('delete-payment-method/', views.DeletePaymentMethodView.as_view(), name='delete_payment_method'),
    path('delete-payment-term/', views.DeletePaymentTermView.as_view(), name='delete_payment_term'),
]