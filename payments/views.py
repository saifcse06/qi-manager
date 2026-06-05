from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
import json
from .models import Payment, PaymentRefund, PaymentHistory
from invoices.models import Invoice
from clients.models import Client
from settings_app.models import PaymentMethod, EmailTemplate, EmailConfiguration, CompanySettings
from .forms import PaymentForm


def _sidebar_context():
    return {
        'payment_count': Payment.objects.filter(is_deleted=False).count(),
        'total_received': Payment.objects.filter(is_deleted=False, status='completed').aggregate(total=Sum('amount'))['total'] or 0,
    }


def get_email_context(obj):
    company_settings = CompanySettings.objects.first()
    return {
        'client_name': obj.invoice.client.company_name if obj.invoice and obj.invoice.client else '',
        'invoice_number': obj.invoice.invoice_number if obj.invoice else '',
        'payment_amount': f"{obj.amount:.2f}",
        'payment_date': obj.payment_date.strftime('%B %d, %Y'),
        'payment_method': obj.payment_method_name,
        'reference_number': obj.reference_number or '',
        'company_name': company_settings.company_name if company_settings else '',
        'signature': '',
    }


def render_template(template_content, context):
    result = template_content
    for key, value in context.items():
        result = result.replace(f'{{{{{key}}}}}', str(value))
    return result


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


class PaymentListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_payment'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.filter(is_deleted=False).select_related('invoice__client', 'payment_method')
        search_query = self.request.GET.get('search')
        invoice_filter = self.request.GET.get('invoice')
        method_filter = self.request.GET.get('method')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if search_query:
            queryset = queryset.filter(
                Q(reference_number__icontains=search_query) |
                Q(invoice__invoice_number__icontains=search_query) |
                Q(invoice__client__company_name__icontains=search_query) |
                Q(payment_method_name__icontains=search_query)
            )
        if invoice_filter:
            queryset = queryset.filter(invoice_id=invoice_filter)
        if method_filter:
            queryset = queryset.filter(payment_method_id=method_filter)
        if status_filter in dict(Payment.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(payment_date__gte=parse_date(date_from))
        if date_to:
            queryset = queryset.filter(payment_date__lte=parse_date(date_to))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['invoice_filter'] = self.request.GET.get('invoice', '')
        context['method_filter'] = self.request.GET.get('method', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['invoices'] = Invoice.objects.filter(is_deleted=False)
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        context['status_choices'] = Payment.STATUS_CHOICES
        return context


class PaymentInvoiceListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list_by_invoice.html'
    context_object_name = 'payments'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_payment'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.invoice = get_object_or_404(Invoice, pk=kwargs['invoice_pk'], is_deleted=False)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False, invoice=self.invoice).select_related('payment_method')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.invoice
        context['total_paid'] = self.invoice.paid_amount
        context['balance_due'] = self.invoice.balance_due
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        return context


class PaymentCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.add_payment'
    success_url = reverse_lazy('payments:payment_list')

    def get_initial(self):
        initial = super().get_initial()
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id, is_deleted=False)
                initial['invoice'] = invoice
            except Invoice.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            try:
                context['invoice'] = Invoice.objects.get(pk=invoice_id, is_deleted=False)
                context['client'] = context['invoice'].client
            except Invoice.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)

        PaymentHistory.objects.create(
            payment=self.object,
            action='create',
            performed_by=self.request.user,
            description=f"Payment of {self.object.amount} recorded for invoice {self.object.invoice.invoice_number}"
        )

        self.object.invoice.update_status_from_payment()

        messages.success(self.request, 'Payment recorded successfully.')
        return response


class PaymentUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.change_payment'
    success_url = reverse_lazy('payments:payment_list')

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False)

    def form_valid(self, form):
        old_data = {
            'amount': str(self.object.amount),
            'status': self.object.status,
            'reference_number': self.object.reference_number or '',
            'remarks': self.object.remarks or '',
        }

        form.instance.updated_by = self.request.user
        response = super().form_valid(form)

        new_data = {
            'amount': str(self.object.amount),
            'status': self.object.status,
            'reference_number': self.object.reference_number or '',
            'remarks': self.object.remarks or '',
        }

        changes = []
        for key in old_data:
            if old_data[key] != new_data[key]:
                changes.append(f"{key} changed from {old_data[key]} to {new_data[key]}")

        action = 'update'
        if old_data['status'] != new_data['status']:
            action = 'status_change'

        PaymentHistory.objects.create(
            payment=self.object,
            action=action,
            performed_by=self.request.user,
            description='; '.join(changes) if changes else "Payment details updated",
            old_values=old_data,
            new_values=new_data,
        )

        self.object.invoice.update_status_from_payment()

        messages.success(self.request, 'Payment updated successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['invoice'] = self.object.invoice
        return context


class PaymentDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Payment
    template_name = 'payments/payment_confirm_delete.html'
    required_roles = ['Super Admin']
    required_permission = 'payments.delete_payment'
    success_url = reverse_lazy('payments:payment_list')

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        invoice = self.object.invoice

        old_amount = self.object.amount
        old_status = self.object.status

        self.object.soft_delete()

        PaymentHistory.objects.create(
            payment=self.object,
            action='delete',
            performed_by=request.user,
            description=f"Payment of {old_amount} for invoice {self.object.invoice.invoice_number} deleted",
        )

        invoice.update_status_from_payment()

        messages.success(request, 'Payment deleted successfully.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class PaymentDetailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_payment'

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['refunds'] = self.object.refunds.filter(is_deleted=False)
        context['history'] = self.object.history.all()
        invoice = self.object.invoice
        context['invoice'] = invoice
        context['balance_due'] = invoice.balance_due
        return context


class PaymentRefundCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PaymentRefund
    fields = ['amount', 'refund_date', 'reference_number', 'reason']
    template_name = 'payments/refund_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.change_payment'

    def dispatch(self, request, *args, **kwargs):
        self.payment = get_object_or_404(Payment, pk=kwargs['payment_pk'], is_deleted=False)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['payment'] = self.payment
        return context

    def form_valid(self, form):
        form.instance.payment = self.payment
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)

        PaymentHistory.objects.create(
            payment=self.payment,
            action='refund',
            performed_by=self.request.user,
            description=f"Refund of {self.object.amount} issued for payment #{self.payment.id}"
        )

        self.payment.invoice.update_status_from_payment()

        messages.success(self.request, 'Refund recorded successfully.')
        return redirect('payments:payment_detail', pk=self.payment.pk)


class PaymentRefundDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PaymentRefund
    template_name = 'payments/refund_confirm_delete.html'
    required_roles = ['Super Admin']
    required_permission = 'payments.change_payment'

    def get_queryset(self):
        return PaymentRefund.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        payment = self.object.payment

        self.object.soft_delete()

        PaymentHistory.objects.create(
            payment=payment,
            action='refund_deleted',
            performed_by=request.user,
            description=f"Refund of {self.object.amount} for payment #{payment.id} deleted",
        )

        payment.invoice.update_status_from_payment()

        messages.success(request, 'Refund deleted successfully.')
        return redirect('payments:payment_detail', pk=payment.pk)


class PaymentReceiptView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_receipt.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_payment'

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        invoice = self.object.invoice
        context['invoice'] = invoice
        context['balance_due'] = invoice.balance_due
        return context


class PaymentReceiptPDFView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_payment'

    def get_queryset(self):
        return Payment.objects.filter(is_deleted=False)

    def get(self, request, *args, **kwargs):
        payment = self.get_object()
        invoice = payment.invoice

        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomGap=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER)

        elements.append(Paragraph("PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 12))

        data = [
            ["Receipt No:", f"PAY-{payment.id:06d}"],
            ["Invoice Number:", invoice.invoice_number],
            ["Client:", invoice.client.company_name],
            ["Payment Date:", payment.payment_date.strftime("%B %d, %Y")],
            ["Payment Method:", payment.payment_method_name],
            ["Reference Number:", payment.reference_number or 'N/A'],
        ]
        table = Table(data, colWidths=[50*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        totals_data = [
            ["Total Invoice Amount:", f"${invoice.total_amount:.2f}"],
            ["Total Paid:", f"${invoice.paid_amount:.2f}"],
            ["This Payment:", f"${payment.amount:.2f}"],
            ["Balance Due:", f"${invoice.balance_due:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[100*mm, 50*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('LINEABOVE', (0,3), (-1,3), 1, colors.black),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 20))

        if payment.remarks:
            elements.append(Paragraph("Remarks:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(payment.remarks, styles['Normal']))
            elements.append(Spacer(1, 20))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your payment!", styles['Normal']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))

        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_PAY-{payment.id:06d}.pdf"'
        return response


class PaymentEmailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.send_payment_receipt'

    def _generate_pdf(self, payment):
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomGap=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER)

        elements.append(Paragraph("PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 12))

        invoice = payment.invoice
        data = [
            ["Receipt No:", f"PAY-{payment.id:06d}"],
            ["Invoice Number:", invoice.invoice_number],
            ["Client:", invoice.client.company_name],
            ["Payment Date:", payment.payment_date.strftime("%B %d, %Y")],
            ["Payment Method:", payment.payment_method_name],
            ["Reference Number:", payment.reference_number or 'N/A'],
        ]
        table = Table(data, colWidths=[50*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        totals_data = [
            ["Total Invoice Amount:", f"${invoice.total_amount:.2f}"],
            ["Total Paid:", f"${invoice.paid_amount:.2f}"],
            ["This Payment:", f"${payment.amount:.2f}"],
            ["Balance Due:", f"${invoice.balance_due:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[100*mm, 50*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('LINEABOVE', (0,3), (-1,3), 1, colors.black),
        ]))
        elements.append(totals_table)

        if payment.remarks:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Remarks:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(payment.remarks, styles['Normal']))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your payment!", styles['Normal']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))

        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, is_deleted=False)

        default_recipient = ''
        if payment.invoice.contact_person and payment.invoice.contact_person.email:
            default_recipient = payment.invoice.contact_person.email
        elif payment.invoice.client.email:
            default_recipient = payment.invoice.client.email

        recipient_email = request.POST.get('recipient_email', default_recipient)
        template_id = request.POST.get('template')
        subject = request.POST.get('subject', f'Payment Receipt for Invoice {payment.invoice.invoice_number}')
        message = request.POST.get('message', '')

        if not recipient_email:
            messages.error(request, 'Recipient email is required.')
            return redirect('payments:payment_detail', pk=pk)

        if template_id:
            try:
                template = EmailTemplate.objects.get(pk=template_id, template_type='payment_receipt', is_active=True)
                context = get_email_context(payment)
                subject = render_template(template.subject, context)
                message = render_template(template.body, context)
            except EmailTemplate.DoesNotExist:
                pass

        pdf_content = self._generate_pdf(payment)

        email_config = EmailConfiguration.objects.first()
        from_email = settings.DEFAULT_FROM_EMAIL
        if email_config and email_config.default_sender_name:
            from_email = f"{email_config.default_sender_name} <{from_email}>"

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[recipient_email],
        )
        email.attach(f'payment_receipt_PAY-{payment.id:06d}.pdf', pdf_content, 'application/pdf')

        try:
            email.send()

            PaymentHistory.objects.create(
                payment=payment,
                action='receipt_sent',
                performed_by=request.user,
                description=f"Payment receipt sent to {recipient_email}"
            )

            messages.success(request, f'Payment receipt sent successfully to {recipient_email}.')
        except Exception as e:
            messages.error(request, f'Failed to send receipt: {str(e)}')

        return redirect('payments:payment_detail', pk=pk)


class PaymentHistoryView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListView):
    model = PaymentHistory
    template_name = 'payments/payment_history.html'
    context_object_name = 'history'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'payments.view_paymenthistory'
    paginate_by = 50

    def get_queryset(self):
        self.payment = get_object_or_404(Payment, pk=self.kwargs['payment_pk'], is_deleted=False)
        return PaymentHistory.objects.filter(payment=self.payment).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['payment'] = self.payment
        context['invoice'] = self.payment.invoice
        return context
