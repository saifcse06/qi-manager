from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Client, ClientContactPerson
from .forms import ClientForm, ClientContactPersonForm


def _sidebar_context():
    return {
        'client_count': Client.objects.filter(is_deleted=False).count(),
        'contact_person_count': ClientContactPerson.objects.filter(is_deleted=False).count(),
    }


class RoleRequiredMixin(UserPassesTestMixin):
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
    """Mixin to check if user has a specific permission codename on their roles."""
    required_permission = None

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        if not self.required_permission:
            return True
        return self.request.user.roles.filter(permissions__codename=self.required_permission).exists()

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')


class ListViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# Client Views
class ClientListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_client'

    def get_queryset(self):
        queryset = Client.objects.filter(is_deleted=False).order_by('-created_at')
        search_query = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(company_registration_no__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        if status_filter in ['active', 'inactive']:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class ClientCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.add_client'

    def form_valid(self, form):
        messages.success(self.request, 'Client created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class ClientUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.change_client'

    def get_queryset(self):
        return Client.objects.filter(is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, 'Client updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class ClientDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')
    required_roles = ['Super Admin']
    required_permission = 'clients.delete_client'

    def get_queryset(self):
        return Client.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, 'Client deleted successfully.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class ClientDetailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_client'

    def get_queryset(self):
        return Client.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['contact_persons'] = self.object.contact_persons.filter(is_deleted=False)
        return context


# Client Contact Person Views
class ClientContactPersonListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = ClientContactPerson
    template_name = 'clients/contact_person_list.html'
    context_object_name = 'contact_persons'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_clientcontactperson'

    def get_queryset(self):
        return ClientContactPerson.objects.select_related('client').filter(is_deleted=False).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ClientContactPersonCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClientContactPerson
    form_class = ClientContactPersonForm
    template_name = 'clients/contact_person_form.html'
    success_url = reverse_lazy('clients:contact_person_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.add_clientcontactperson'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not kwargs.get('instance'):
            initial_client = self.request.GET.get('client')
            if initial_client:
                kwargs['initial'] = {'client': initial_client}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        pre_selected_client = self.request.GET.get('client')
        if pre_selected_client:
            context['pre_selected_client'] = pre_selected_client
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Contact person created successfully.')
        return super().form_valid(form)


class ClientContactPersonUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ClientContactPerson
    form_class = ClientContactPersonForm
    template_name = 'clients/contact_person_form.html'
    success_url = reverse_lazy('clients:contact_person_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.change_clientcontactperson'

    def form_valid(self, form):
        messages.success(self.request, 'Contact person updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class ClientContactPersonDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ClientContactPerson
    template_name = 'clients/contact_person_confirm_delete.html'
    success_url = reverse_lazy('clients:contact_person_list')
    required_roles = ['Super Admin']
    required_permission = 'clients.delete_clientcontactperson'

    def get_queryset(self):
        return ClientContactPerson.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, 'Contact person deleted successfully.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


# AJAX Views
class ClientContactPersonDatatableView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_clientcontactperson'

    def get(self, request):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_col = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'desc')

        queryset = ClientContactPerson.objects.select_related('client').filter(is_deleted=False, client__is_deleted=False)

        if search_value:
            queryset = queryset.filter(
                Q(person_name__icontains=search_value) |
                Q(designation__icontains=search_value) |
                Q(department__icontains=search_value) |
                Q(mobile_number__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(client__company_name__icontains=search_value)
            )

        total_count = ClientContactPerson.objects.filter(is_deleted=False, client__is_deleted=False).count()
        filtered_count = queryset.count()

        order_fields = ['client__company_name', 'person_name', 'designation', 'mobile_number', 'status']
        if order_col < len(order_fields):
            order_field = order_fields[order_col]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)

        queryset = queryset[start:start + length]

        data = []
        for cp in queryset:
            data.append({
                'id': cp.pk,
                'client_name': cp.client.company_name,
                'person_name': cp.person_name,
                'designation': cp.designation or '',
                'mobile': cp.mobile_number or '',
                'status': '<span class="badge bg-success-subtle text-success">Active</span>' if cp.status == 'active' else '<span class="badge bg-danger-subtle text-danger">Inactive</span>',
                'is_primary': '<i class="fas fa-star text-warning"></i>' if cp.is_primary else '',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data,
        }, status=200)


class ClientDatatableView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_client'

    def get(self, request):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_col = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'desc')

        queryset = Client.objects.filter(is_deleted=False)

        if search_value:
            queryset = queryset.filter(
                Q(company_name__icontains=search_value) |
                Q(company_registration_no__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(phone__icontains=search_value)
            )

        total_count = Client.objects.filter(is_deleted=False).count()
        filtered_count = queryset.count()

        order_fields = ['company_name', 'email', 'phone', 'status']
        if order_col < len(order_fields):
            order_field = order_fields[order_col]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)

        queryset = queryset[start:start + length]

        data = []
        for client in queryset:
            contact_persons = client.contact_persons.filter(status='active', is_deleted=False).count()
            data.append({
                'id': client.pk,
                'company_name': client.company_name,
                'registration_no': client.company_registration_no or '',
                'email': client.email or '',
                'phone': client.phone or '',
                'status': '<span class="badge bg-success-subtle text-success">Active</span>' if client.status == 'active' else '<span class="badge bg-danger-subtle text-danger">Inactive</span>',
                'contact_persons': contact_persons,
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data,
        }, status=200)


class LoadContactPersonsView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'clients.view_clientcontactperson'

    def get(self, request):
        client_id = request.GET.get('client')
        if client_id:
            contact_persons = ClientContactPerson.objects.filter(
                client_id=client_id, 
                is_deleted=False
            ).values('id', 'person_name')
        else:
            contact_persons = []
        
        return JsonResponse({
            'contact_persons': list(contact_persons)
        })
