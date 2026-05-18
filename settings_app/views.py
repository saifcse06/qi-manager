from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from accounts.views import PermissionRequiredMixin
from .models import (
    CompanySettings, EmailConfiguration, EmailTemplate,
    QuotationConfiguration, InvoiceConfiguration, PaymentMethod, PaymentTerm,
)
from .forms import (
    CompanySettingsForm, EmailConfigurationForm, EmailTemplateForm,
    QuotationConfigurationForm, InvoiceConfigurationForm,
    PaymentMethodForm, PaymentTermForm,
)


def _get_or_create(model):
    """Get first instance or return empty instance for singleton models."""
    if model.objects.exists():
        return model.objects.first()
    return model()


class SettingsDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Main System Settings dashboard with tab-based navigation."""
    template_name = 'settings_app/settings_dashboard.html'
    required_permission = 'settings_app.view_settings'

    def get(self, request, *args, **kwargs):
        """Handle GET requests - render forms with current settings data."""
        active_tab = request.GET.get('tab', 'company')

        context = {
            'active_tab': active_tab,
            'company_settings': _get_or_create(CompanySettings),
            'email_config': _get_or_create(EmailConfiguration),
            'quotation_config': _get_or_create(QuotationConfiguration),
            'invoice_config': _get_or_create(InvoiceConfiguration),
            'payment_methods': PaymentMethod.objects.all().order_by('sort_order', 'name'),
            'payment_terms': PaymentTerm.objects.all().order_by('sort_order', 'name'),
            'email_templates': EmailTemplate.objects.all().order_by('template_type'),
            'total_payment_methods': PaymentMethod.objects.count(),
            'total_payment_terms': PaymentTerm.objects.count(),
            'total_email_templates': EmailTemplate.objects.count(),
        }

        # Instantiate forms with current data for initial rendering
        instance = _get_or_create(CompanySettings)
        context['company_settings_form'] = CompanySettingsForm(instance=instance)

        instance = _get_or_create(EmailConfiguration)
        context['email_config_form'] = EmailConfigurationForm(instance=instance)

        context['email_template_form'] = EmailTemplateForm()

        instance = _get_or_create(QuotationConfiguration)
        context['quotation_config_form'] = QuotationConfigurationForm(instance=instance)

        instance = _get_or_create(InvoiceConfiguration)
        context['invoice_config_form'] = InvoiceConfigurationForm(instance=instance)

        context['payment_method_form'] = PaymentMethodForm()
        context['payment_term_form'] = PaymentTermForm()

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle all POST requests for settings form submissions."""
        if not request.user.has_permission('settings_app.change_settings'):
            messages.error(request, "You don't have permission to modify settings.")
            return redirect(f'{request.path}?tab={request.POST.get("active_tab", "company")}')

        active_tab = request.POST.get('active_tab', 'company')
        handler_map = {
            'company': self._handle_company,
            'email': self._handle_email,
            'templates': self._handle_template,
            'quotation': self._handle_quotation,
            'invoice': self._handle_invoice,
            'payment-method': self._handle_payment_method,
            'payment-term': self._handle_payment_term,
        }
        handler = handler_map.get(active_tab)
        if handler:
            response = handler(request)
            if response:
                return response
        return redirect(f'{request.path}?tab={active_tab}')

    def _handle_company(self, request):
        """Save company settings."""
        instance = _get_or_create(CompanySettings)
        form = CompanySettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company settings updated successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_email(self, request):
        """Save email configuration."""
        instance = _get_or_create(EmailConfiguration)
        form = EmailConfigurationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email configuration updated successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_template(self, request):
        """Save email template."""
        template_id = request.POST.get('template_id')
        kwargs = {}
        if template_id:
            kwargs['instance'] = get_object_or_404(EmailTemplate, id=template_id)
        form = EmailTemplateForm(request.POST, **kwargs)
        if form.is_valid():
            obj = form.save()
            action = 'updated' if template_id else 'created'
            messages.success(request, f'Email template {action} successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_quotation(self, request):
        """Save quotation configuration."""
        instance = _get_or_create(QuotationConfiguration)
        form = QuotationConfigurationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quotation configuration updated successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_invoice(self, request):
        """Save invoice configuration."""
        instance = _get_or_create(InvoiceConfiguration)
        form = InvoiceConfigurationForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice configuration updated successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_payment_method(self, request):
        """Save payment method (create or update)."""
        method_id = request.POST.get('method_id')
        kwargs = {}
        is_update = bool(method_id)
        if method_id:
            try:
                kwargs['instance'] = PaymentMethod.objects.get(id=method_id)
            except PaymentMethod.DoesNotExist:
                pass
        form = PaymentMethodForm(request.POST, **kwargs)
        if form.is_valid():
            # Ensure only one default
            if form.cleaned_data.get('is_default'):
                PaymentMethod.objects.filter(is_default=True).exclude(id=method_id).update(is_default=False)
            form.save()
            action = 'updated' if is_update else 'created'
            messages.success(request, f'Payment method {action} successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    def _handle_payment_term(self, request):
        """Save payment term (create or update)."""
        term_id = request.POST.get('term_id')
        kwargs = {}
        is_update = bool(term_id)
        if term_id:
            try:
                kwargs['instance'] = PaymentTerm.objects.get(id=term_id)
            except PaymentTerm.DoesNotExist:
                pass
        form = PaymentTermForm(request.POST, **kwargs)
        if form.is_valid():
            # Ensure only one default
            if form.cleaned_data.get('is_default'):
                PaymentTerm.objects.filter(is_default=True).exclude(id=term_id).update(is_default=False)
            form.save()
            action = 'updated' if is_update else 'created'
            messages.success(request, f'Payment term {action} successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')


class DeletePaymentMethodView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_permission('settings_app.delete_paymentmethod'):
            messages.error(request, "You don't have permission to delete payment methods.")
            return redirect('settings_app:settings_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        method_id = request.POST.get('id')
        try:
            method = PaymentMethod.objects.get(id=method_id)
            method.delete()
            messages.success(request, 'Payment method deleted successfully.')
        except PaymentMethod.DoesNotExist:
            messages.error(request, 'Payment method not found.')
        return HttpResponseRedirect(reverse('settings_app:settings_dashboard') + '?tab=payment-method')


class DeletePaymentTermView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_permission('settings_app.delete_paymentterm'):
            messages.error(request, "You don't have permission to delete payment terms.")
            return redirect('settings_app:settings_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        term_id = request.POST.get('id')
        try:
            term = PaymentTerm.objects.get(id=term_id)
            term.delete()
            messages.success(request, 'Payment term deleted successfully.')
        except PaymentTerm.DoesNotExist:
            messages.error(request, 'Payment term not found.')
        return HttpResponseRedirect(reverse('settings_app:settings_dashboard') + '?tab=payment-method')