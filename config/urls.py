from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import (
    index_view, HomeView, ProfileView,
    UserListView, UserCreateView, UserUpdateView, UserDeleteView, UserDetailView,
    RoleListView, RoleCreateView, RoleUpdateView, RoleDeleteView, RoleDetailView,
    PermissionListView, PermissionCreateView, PermissionUpdateView, PermissionDeleteView, PermissionDetailView,
    UserDatatableView, RoleDatatableView, PermissionDatatableView,
    LoadRolesView, LoadPermissionsView,
)
from clients.views import ClientDatatableView, ClientContactPersonDatatableView

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # Allauth URLs - MUST come before accounts app to handle /accounts/* routes
    path('accounts/', include('allauth.urls')),

    # Custom accounts CRUD URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role_detail'),
    path('roles/<int:pk>/update/', RoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', RoleDeleteView.as_view(), name='role_delete'),

    path('permissions/', PermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', PermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<int:pk>/', PermissionDetailView.as_view(), name='permission_detail'),
    path('permissions/<int:pk>/update/', PermissionUpdateView.as_view(), name='permission_update'),
    path('permissions/<int:pk>/delete/', PermissionDeleteView.as_view(), name='permission_delete'),

    # AJAX URLs
    path('ajax/load-roles/', LoadRolesView.as_view(), name='ajax_load_roles'),
    path('ajax/load-permissions/', LoadPermissionsView.as_view(), name='ajax_load_permissions'),

    # DataTable AJAX endpoints
    path('ajax/users-datatable/', UserDatatableView.as_view(), name='users_datatable'),
    path('ajax/roles-datatable/', RoleDatatableView.as_view(), name='roles_datatable'),
    path('ajax/permissions-datatable/', PermissionDatatableView.as_view(), name='permissions_datatable'),
    path('ajax/clients-datatable/', ClientDatatableView.as_view(), name='clients_datatable'),
    path('ajax/contact-persons-datatable/', ClientContactPersonDatatableView.as_view(), name='contact_persons_datatable'),

# Client Management URLs
    path('clients/', include('clients.urls', namespace='clients')),
    
    # Products Management URLs
    path('products/', include('products.urls', namespace='products')),
    
    # System Settings URLs
    path('settings/', include('settings_app.urls', namespace='settings_app')),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Main pages
    path('', index_view, name='index'),
    path('home/', HomeView.as_view(), name='home'),
    path('profile/', ProfileView.as_view(), name='profile'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)