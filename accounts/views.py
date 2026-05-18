from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from .models import User, Role, Permission
from .forms import CustomUserCreationForm, CustomUserChangeForm, RoleForm, PermissionForm


def index_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')


def _sidebar_context():
    """Helper to provide sidebar badge counts."""
    return {
        'user_count': User.objects.count(),
        'role_count': Role.objects.count(),
        'permission_count': Permission.objects.count(),
    }


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['total_users'] = context['user_count']
        context['total_roles'] = context['role_count']
        context['total_permissions'] = context['permission_count']
        context['active_users'] = User.objects.filter(is_active=True).count()
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# Mixins for permission checking
class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user has required role(s)"""
    required_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        if not self.required_roles:
            return True
        return self.request.user.roles.filter(name__in=self.required_roles).exists()

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')


class PermissionRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user has required permission"""
    required_permission = None

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        if not self.required_permission:
            return True
        return self.request.user.has_permission(self.required_permission)

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')


class ListViewMixin:
    """Mixin to add sidebar context to all list views."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# User Views
class UserListView(LoginRequiredMixin, RoleRequiredMixin, ListViewMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    required_roles = ['Super Admin', 'Admin']

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class UserCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'User created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class UserUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class UserDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    required_roles = ['Super Admin']

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'User deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class UserDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user'
    required_roles = ['Super Admin', 'Admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# Role Views
class RoleListView(LoginRequiredMixin, RoleRequiredMixin, ListViewMixin, ListView):
    model = Role
    template_name = 'accounts/role_list.html'
    context_object_name = 'roles'
    required_roles = ['Super Admin', 'Admin']

    def get_queryset(self):
        queryset = Role.objects.all().order_by('name')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class RoleCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('role_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'Role created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class RoleUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('role_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'Role updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class RoleDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Role
    template_name = 'accounts/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')
    required_roles = ['Super Admin']

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Role deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class RoleDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Role
    template_name = 'accounts/role_detail.html'
    context_object_name = 'role'
    required_roles = ['Super Admin', 'Admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# Permission Views
class PermissionListView(LoginRequiredMixin, RoleRequiredMixin, ListViewMixin, ListView):
    model = Permission
    template_name = 'accounts/permission_list.html'
    context_object_name = 'permissions'
    required_roles = ['Super Admin', 'Admin']

    def get_queryset(self):
        queryset = Permission.objects.all().order_by('codename')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(codename__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PermissionCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'accounts/permission_form.html'
    success_url = reverse_lazy('permission_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'Permission created successfully.')
        return super().form_valid(form)


class PermissionUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'accounts/permission_form.html'
    success_url = reverse_lazy('permission_list')
    required_roles = ['Super Admin', 'Admin']

    def form_valid(self, form):
        messages.success(self.request, 'Permission updated successfully.')
        return super().form_valid(form)


class PermissionDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Permission
    template_name = 'accounts/permission_confirm_delete.html'
    success_url = reverse_lazy('permission_list')
    required_roles = ['Super Admin']

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Permission deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PermissionDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Permission
    template_name = 'accounts/permission_detail.html'
    context_object_name = 'permission'
    required_roles = ['Super Admin', 'Admin']


# AJAX DataTable Views
class UserDatatableView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Server-side DataTables endpoint for users."""
    required_roles = ['Super Admin', 'Admin']

    def get(self, request):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_col = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'desc')

        queryset = User.objects.all()

        # Search
        if search_value:
            queryset = queryset.filter(
                Q(username__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value)
            )

        # Count total and filtered
        total_count = User.objects.count()
        filtered_count = queryset.count()

        # Ordering
        order_fields = ['-date_joined', 'username', 'email', 'first_name', 'last_name', 'is_active']
        if order_col < len(order_fields):
            order_field = order_fields[order_col]
            if order_dir == 'asc':
                order_field = order_field.lstrip('-')
            else:
                if not order_field.startswith('-'):
                    order_field = '-' + order_field
            queryset = queryset.order_by(order_field)

        # Pagination
        queryset = queryset[start:start + length]

        data = []
        for user in queryset:
            roles = ', '.join(user.roles.values_list('name', flat=True))
            data.append({
                'id': user.pk,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'email': user.email,
                'roles': roles if roles else '<span class="badge bg-light text-muted">No Roles</span>',
                'is_active': '<span class="badge bg-success-subtle text-success">Active</span>' if user.is_active else '<span class="badge bg-danger-subtle text-danger">Inactive</span>',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data,
        }, status=200)


class RoleDatatableView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Server-side DataTables endpoint for roles."""
    required_roles = ['Super Admin', 'Admin']

    def get(self, request):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_col = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        queryset = Role.objects.all()

        # Search
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(description__icontains=search_value)
            )

        total_count = Role.objects.count()
        filtered_count = queryset.count()

        # Ordering
        order_fields = ['name', 'description']
        if order_col < len(order_fields):
            order_field = order_fields[order_col]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)

        # Pagination
        queryset = queryset[start:start + length]

        data = []
        for role in queryset:
            data.append({
                'id': role.pk,
                'name': role.name,
                'description': role.description or '',
                'permissions': role.permissions.count(),
                'users': role.users.count(),
                'created_at': role.created_at.strftime('%b %d, %Y') if role.created_at else '',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data,
        }, status=200)


class PermissionDatatableView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Server-side DataTables endpoint for permissions."""
    required_roles = ['Super Admin', 'Admin']

    def get(self, request):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_col = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        queryset = Permission.objects.all()

        # Search
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(codename__icontains=search_value) |
                Q(description__icontains=search_value)
            )

        total_count = Permission.objects.count()
        filtered_count = queryset.count()

        # Ordering
        order_fields = ['name', 'codename', 'description']
        if order_col < len(order_fields):
            order_field = order_fields[order_col]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)

        # Pagination
        queryset = queryset[start:start + length]

        data = []
        for perm in queryset:
            roles = ', '.join(perm.roles.values_list('name', flat=True))
            data.append({
                'id': perm.pk,
                'name': perm.name,
                'codename': perm.codename,
                'description': perm.description or '',
                'roles': roles if roles else 'Unassigned',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data,
        }, status=200)


# AJAX Views for dynamic form loading
class LoadRolesView(LoginRequiredMixin, View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            roles = list(user.roles.values('id', 'name'))
            return JsonResponse({'roles': roles})
        return JsonResponse({'roles': []})


class LoadPermissionsView(LoginRequiredMixin, View):
    def get(self, request):
        role_id = request.GET.get('role_id')
        if role_id:
            role = get_object_or_404(Role, id=role_id)
            permissions = list(role.permissions.values('id', 'name', 'codename'))
            return JsonResponse({'permissions': permissions})
        return JsonResponse({'permissions': []})