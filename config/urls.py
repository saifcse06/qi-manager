from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from accounts.views import index_view, HomeView, ProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', index_view, name='index'),
    path('home/', HomeView.as_view(), name='home'),
    path('profile/', ProfileView.as_view(), name='profile'),
]