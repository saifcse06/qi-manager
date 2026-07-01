from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
import logging
from accounts.views import (
    PermissionRequiredMixin, _sidebar_context
)
from .models import (
    CompanySettings, EmailConfiguration, EmailTemplate,
    QuotationConfiguration, InvoiceConfiguration, PaymentMethod, PaymentTerm,
)
from .forms import (
    CompanySettingsForm, EmailConfigurationForm, EmailTemplateForm,
    QuotationConfigurationForm, InvoiceConfigurationForm,
    PaymentMethodForm, PaymentTermForm,
)

logger = logging.getLogger('settings_app')


def _get_or_create(model):
    """Get first instance or return empty instance for singleton models."""
    instance = model.objects.first()
    if instance is not None:
        return instance
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
        context.update(_sidebar_context())

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
            logger.warning('Permission denied for user=%s on settings POST', request.user.username)
            messages.error(request, "You don't have permission to modify settings.")
            return redirect(f'{request.path}?tab={request.POST.get("active_tab", "company")}')

        active_tab = request.POST.get('active_tab', 'company')
        logger.debug('Settings POST received user=%s tab=%s', request.user.username, active_tab)
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
            try:
                response = handler(request)
            except Exception as exc:
                logger.exception('Unexpected error in %s handler user=%s error=%s', active_tab, request.user.username, exc)
                messages.error(request, 'An unexpected error occurred. Check logs for details.')
                response = None
            if response:
                return response
        return redirect(f'{request.path}?tab={active_tab}')

    def _handle_company(self, request):
        """Save company settings."""
        instance = _get_or_create(CompanySettings)
        form = CompanySettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            logger.info('Company settings updated by user=%s pk=%s name=%s', request.user.username, obj.pk, obj.company_name)
            messages.success(request, 'Company settings updated successfully.')
        else:
            logger.warning('Company settings validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
            messages.error(request, 'Please correct the errors below.')

    def _handle_email(self, request):
        """Save email configuration."""
        instance = _get_or_create(EmailConfiguration)
        form = EmailConfigurationForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            logger.info('Email config updated by user=%s pk=%s host=%s', request.user.username, obj.pk, obj.smtp_host)
            messages.success(request, 'Email configuration updated successfully.')
        else:
            logger.warning('Email config validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
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
            logger.info('Email template %s by user=%s pk=%s type=%s', action, request.user.username, obj.pk, obj.template_type)
            messages.success(request, f'Email template {action} successfully.')
        else:
            logger.warning('Email template validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
            messages.error(request, 'Please correct the errors below.')

    def _handle_quotation(self, request):
        """Save quotation configuration."""
        instance = _get_or_create(QuotationConfiguration)
        form = QuotationConfigurationForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            logger.info('Quotation config updated by user=%s pk=%s format=%s', request.user.username, obj.pk, obj.number_format)
            messages.success(request, 'Quotation configuration updated successfully.')
        else:
            logger.warning('Quotation config validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
            messages.error(request, 'Please correct the errors below.')

    def _handle_invoice(self, request):
        """Save invoice configuration."""
        instance = _get_or_create(InvoiceConfiguration)
        form = InvoiceConfigurationForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            logger.info('Invoice config updated by user=%s pk=%s format=%s', request.user.username, obj.pk, obj.number_format)
            messages.success(request, 'Invoice configuration updated successfully.')
        else:
            logger.warning('Invoice config validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
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
            if form.cleaned_data.get('is_default'):
                PaymentMethod.objects.filter(is_default=True).exclude(id=method_id).update(is_default=False)
            obj = form.save()
            action = 'updated' if is_update else 'created'
            logger.info('Payment method %s by user=%s pk=%s name=%s', action, request.user.username, obj.pk, obj.name)
            messages.success(request, f'Payment method {action} successfully.')
        else:
            logger.warning('Payment method validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
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
            if form.cleaned_data.get('is_default'):
                PaymentTerm.objects.filter(is_default=True).exclude(id=term_id).update(is_default=False)
            obj = form.save()
            action = 'updated' if is_update else 'created'
            logger.info('Payment term %s by user=%s pk=%s name=%s', action, request.user.username, obj.pk, obj.name)
            messages.success(request, f'Payment term {action} successfully.')
        else:
            logger.warning('Payment term validation failed for user=%s errors=%s', request.user.username, form.errors.as_json())
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