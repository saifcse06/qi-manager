from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    paginate_by = 10
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
    paginate_by = 10
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
    paginate_by = 10
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