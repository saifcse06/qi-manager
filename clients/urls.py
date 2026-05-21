from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Client URLs
    path('', views.ClientListView.as_view(), name='client_list'),
    path('create/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    
    # Client Contact Person URLs
    path('contact-persons/', views.ClientContactPersonListView.as_view(), name='contact_person_list'),
    path('contact-persons/create/', views.ClientContactPersonCreateView.as_view(), name='contact_person_create'),
    path('contact-persons/<int:pk>/update/', views.ClientContactPersonUpdateView.as_view(), name='contact_person_update'),
    path('contact-persons/<int:pk>/delete/', views.ClientContactPersonDeleteView.as_view(), name='contact_person_delete'),
]