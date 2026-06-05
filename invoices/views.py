from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import os
import json
from .models import Invoice, InvoiceItem, InvoiceHistory
from clients.models import Client, ClientContactPerson
from quotations.models import Quotation
from products.models import Product
from .forms import InvoiceForm, InvoiceItemForm
from settings_app.models import EmailTemplate, EmailConfiguration
from datetime import datetime


def _sidebar_context():
    return {
        'invoice_count': Invoice.objects.filter(is_deleted=False).count(),
    }


def get_email_context(obj):
    """Get context for email template rendering."""
    from settings_app.models import CompanySettings
    company_settings = CompanySettings.objects.first()
    return {
        'client_name': obj.client.company_name if obj.client else '',
        'invoice_number': obj.invoice_number if hasattr(obj, 'invoice_number') else '',
        'quotation_number': obj.quotation_number if hasattr(obj, 'quotation_number') else '',
        'due_amount': f"{obj.balance_due:.2f}" if hasattr(obj, 'balance_due') else '',
        'company_name': company_settings.company_name if company_settings else '',
        'signature': '',
    }


def render_template(template_content, context):
    """Replace template variables with actual values."""
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


class InvoiceListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.view_invoice'

    def get_queryset(self):
        queryset = Invoice.objects.filter(is_deleted=False).order_by('-created_at')
        search_query = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        client_filter = self.request.GET.get('client')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(client__company_name__icontains=search_query) |
                Q(contact_person__person_name__icontains=search_query)
            )
        if status_filter in dict(Invoice.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)
        if client_filter:
            queryset = queryset.filter(client_id=client_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['client_filter'] = self.request.GET.get('client', '')
        context['clients'] = Client.objects.filter(is_deleted=False)
        return context


class InvoiceCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = reverse_lazy('invoices:invoice_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.add_invoice'

    def get_initial(self):
        initial = super().get_initial()
        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            try:
                quotation = Quotation.objects.get(pk=quotation_id, is_deleted=False)
                initial['quotation'] = quotation
                initial['client'] = quotation.client
                if quotation.contact_person:
                    initial['contact_person'] = quotation.contact_person
            except Quotation.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            try:
                context['source_quotation'] = Quotation.objects.get(pk=quotation_id, is_deleted=False)
            except Quotation.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        from django.utils.crypto import get_random_string
        import datetime

        today = datetime.date.today()
        random_str = get_random_string(length=6).upper()
        invoice_number = f"INV-{today.strftime('%Y%m%d')}-{random_str}"

        # Handle quotation from GET parameter (when hidden field is used)
        quotation_id = self.request.GET.get('quotation') or self.request.POST.get('quotation')
        quotation = None
        if quotation_id:
            try:
                quotation = Quotation.objects.get(pk=quotation_id, is_deleted=False)
                form.instance.quotation = quotation
                form.instance.client = quotation.client
                if quotation.contact_person:
                    form.instance.contact_person = quotation.contact_person
            except Quotation.DoesNotExist:
                pass

        form.instance.invoice_number = invoice_number
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        response = super().form_valid(form)

        # If created from quotation, copy items and update quotation status
        if quotation:
            for item in quotation.items.all():
                InvoiceItem.objects.create(
                    invoice=self.object,
                    product=item.product,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_percentage=item.discount_percentage,
                    tax_percentage=item.tax_percentage,
                )
            # Copy discount and tax from quotation
            self.object.discount_amount = quotation.discount_amount
            self.object.tax_amount = quotation.tax_amount
            self.object.notes = quotation.notes or ''
            self.object.terms_conditions = quotation.terms_conditions or ''
            self.object.save()

            # Update quotation status
            quotation.status = 'converted'
            quotation.updated_by = self.request.user
            quotation.save()

        # Create history entry
        InvoiceHistory.objects.create(
            invoice=self.object,
            action='create',
            performed_by=self.request.user,
            description=f"Invoice {self.object.invoice_number} created"
        )

        if quotation:
            InvoiceHistory.objects.create(
                invoice=self.object,
                action='converted_from_quotation',
                performed_by=self.request.user,
                description=f"Converted from Quotation {quotation.quotation_number}"
            )

        messages.success(self.request, 'Invoice created successfully.')
        return response


class InvoiceUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = reverse_lazy('invoices:invoice_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.change_invoice'

    def get_queryset(self):
        return Invoice.objects.filter(is_deleted=False)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # Track changes for history
        if self.object.pk:
            old_status = self.object.status
            old_notes = self.object.notes
            old_terms = self.object.terms_conditions
            old_paid = self.object.paid_amount

            response = super().form_valid(form)

            # Create history entries for changes
            changes = []
            if old_status != self.object.status:
                changes.append(f"Status changed from {dict(Invoice.STATUS_CHOICES)[old_status]} to {dict(Invoice.STATUS_CHOICES)[self.object.status]}")
            if old_notes != self.object.notes:
                changes.append("Notes updated")
            if old_terms != self.object.terms_conditions:
                changes.append("Terms and Conditions updated")
            if old_paid != self.object.paid_amount:
                changes.append(f"Payment amount changed from ${old_paid} to ${self.object.paid_amount}")

            if changes:
                InvoiceHistory.objects.create(
                    invoice=self.object,
                    action='update',
                    performed_by=self.request.user,
                    description="; ".join(changes)
                )

            # Handle status changes
            if old_status != self.object.status:
                InvoiceHistory.objects.create(
                    invoice=self.object,
                    action='status_change',
                    performed_by=self.request.user,
                    description=f"Status changed from {dict(Invoice.STATUS_CHOICES)[old_status]} to {dict(Invoice.STATUS_CHOICES)[self.object.status]}"
                )

            # Handle payment received
            if old_paid != self.object.paid_amount and self.object.paid_amount > old_paid:
                InvoiceHistory.objects.create(
                    invoice=self.object,
                    action='payment_received',
                    performed_by=self.request.user,
                    description=f"Payment of ${self.object.paid_amount - old_paid} received. Total paid: ${self.object.paid_amount}"
                )
                self.object.update_status_from_payment()
        else:
            response = super().form_valid(form)

        messages.success(self.request, 'Invoice updated successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class InvoiceDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoices:invoice_list')
    required_roles = ['Super Admin']
    required_permission = 'invoices.delete_invoice'

    def get_queryset(self):
        return Invoice.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()

        # Create history entry
        InvoiceHistory.objects.create(
            invoice=self.object,
            action='delete',
            performed_by=request.user,
            description=f"Invoice {self.object.invoice_number} soft deleted"
        )

        messages.success(request, 'Invoice deleted successfully.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class InvoiceDetailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.view_invoice'

    def get_queryset(self):
        return Invoice.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['items'] = self.object.items.all()
        context['history'] = self.object.history.all()[:10]
        context['payment_history'] = self.object.history.filter(action='payment_received').order_by('-timestamp')
        context['email_templates'] = EmailTemplate.objects.filter(is_active=True).exclude(template_type='quotation')
        templates_list = []
        for t in context['email_templates']:
            templates_list.append({
                'id': str(t.pk),
                'name': t.get_template_type_display(),
                'subject': t.subject,
                'body': t.body,
            })
        context['email_templates_json'] = json.dumps(templates_list)
        return context


class InvoiceItemCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = InvoiceItem
    form_class = InvoiceItemForm
    template_name = 'invoices/invoiceitem_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.add_invoiceitem'

    def form_valid(self, form):
        form.instance.invoice_id = self.kwargs['invoice_pk']
        response = super().form_valid(form)

        # Create history entry
        invoice = self.object.invoice
        InvoiceHistory.objects.create(
            invoice=invoice,
            action='update',
            performed_by=self.request.user,
            description=f"Item {self.object.product.name} added to invoice"
        )

        messages.success(self.request, 'Item added successfully.')
        return response

    def get_success_url(self):
        return reverse('invoices:invoice_detail', kwargs={'pk': self.kwargs['invoice_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['invoice'] = get_object_or_404(Invoice, pk=self.kwargs['invoice_pk'])
        return context


class InvoiceItemUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = InvoiceItem
    form_class = InvoiceItemForm
    template_name = 'invoices/invoiceitem_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.change_invoiceitem'

    def get_queryset(self):
        return InvoiceItem.objects.filter(invoice__is_deleted=False)

    def form_valid(self, form):
        self.object = form.save()

        # Create history entry
        invoice = self.object.invoice
        InvoiceHistory.objects.create(
            invoice=invoice,
            action='update',
            performed_by=self.request.user,
            description=f"Item {self.object.product.name} updated in invoice"
        )

        messages.success(self.request, 'Item updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('invoices:invoice_detail', kwargs={'pk': self.object.invoice.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['invoice'] = self.object.invoice
        return context


class InvoiceItemDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = InvoiceItem
    template_name = 'invoices/invoiceitem_confirm_delete.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.delete_invoiceitem'

    def get_queryset(self):
        return InvoiceItem.objects.filter(invoice__is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        invoice = self.object.invoice
        item_description = f"{self.object.product.name} x {self.object.quantity}"

        self.object.delete()

        # Create history entry
        InvoiceHistory.objects.create(
            invoice=invoice,
            action='update',
            performed_by=request.user,
            description=f"Item {item_description} removed from invoice"
        )

        messages.success(request, 'Item deleted successfully.')
        return redirect('invoices:invoice_detail', pk=invoice.pk)

    def get_success_url(self):
        return reverse('invoices:invoice_detail', kwargs={'pk': self.object.invoice.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['invoice'] = self.object.invoice
        return context


class InvoicePDFView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_pdf.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.view_invoice'

    def get_queryset(self):
        return Invoice.objects.filter(is_deleted=False)

    def render_to_response(self, context, **response_kwargs):
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomGap=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Title
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 12))

        # Invoice number and date
        invoice = self.object
        data = [
            ["Invoice Number:", invoice.invoice_number],
            ["Date:", invoice.created_at.strftime("%B %d, %Y")],
            ["Due Date:", invoice.due_date.strftime("%B %d, %Y") if invoice.due_date else "N/A"],
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

        # Bill To
        elements.append(Paragraph("Bill To:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        bill_to_data = [
            [invoice.client.company_name],
            [invoice.client.address or ''],
            [f"Email: {invoice.client.email or ''}"],
            [f"Phone: {invoice.client.phone or ''}"],
        ]
        bill_to_table = Table(bill_to_data, colWidths=[150*mm])
        bill_to_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(bill_to_table)
        elements.append(Spacer(1, 12))

        # Items table
        elements.append(Paragraph("Items:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        items_data = [["#", "Description", "Qty", "Unit Price", "Discount", "Tax", "Total"]]
        for i, item in enumerate(invoice.items.all(), start=1):
            items_data.append([
                str(i),
                f"{item.product.name}\n{item.description or ''}",
                f"{item.quantity}",
                f"${item.unit_price:.2f}",
                f"{item.discount_percentage:.2f}%",
                f"{item.tax_percentage:.2f}%",
                f"${item.total_price:.2f}",
            ])
        items_table = Table(items_data, colWidths=[10*mm, 60*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        # Totals
        elements.append(Paragraph("Totals:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        totals_data = [
            ["Subtotal:", f"${invoice.subtotal:.2f}"],
            ["Discount:", f"-${invoice.discount_amount:.2f}"],
            ["Tax:", f"+${invoice.tax_amount:.2f}"],
            ["Total:", f"${invoice.total_amount:.2f}"],
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

        # Payment info
        elements.append(Spacer(1, 12))
        payment_data = [
            ["Paid Amount:", f"${invoice.paid_amount:.2f}"],
            ["Balance Due:", f"${invoice.balance_due:.2f}"],
        ]
        payment_table = Table(payment_data, colWidths=[100*mm, 50*mm])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))

        if invoice.notes:
            elements.append(Paragraph("Notes:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(invoice.notes, styles['Normal']))
            elements.append(Spacer(1, 12))

        if invoice.terms_conditions:
            elements.append(Paragraph("Terms & Conditions:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(invoice.terms_conditions, styles['Normal']))
            elements.append(Spacer(1, 12))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your business!", styles['Normal']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))

        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response


class InvoiceEmailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.send_invoice'

    def _generate_pdf(self, invoice):
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomGap=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Title
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 12))

        data = [
            ["Invoice Number:", invoice.invoice_number],
            ["Date:", invoice.created_at.strftime("%B %d, %Y")],
            ["Due Date:", invoice.due_date.strftime("%B %d, %Y") if invoice.due_date else "N/A"],
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

        elements.append(Paragraph("Bill To:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        bill_to_data = [
            [invoice.client.company_name],
            [invoice.client.address or ''],
            [f"Email: {invoice.client.email or ''}"],
            [f"Phone: {invoice.client.phone or ''}"],
        ]
        bill_to_table = Table(bill_to_data, colWidths=[150*mm])
        bill_to_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(bill_to_table)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Items:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        items_data = [["#", "Description", "Qty", "Unit Price", "Discount", "Tax", "Total"]]
        for i, item in enumerate(invoice.items.all(), start=1):
            items_data.append([
                str(i),
                f"{item.product.name}\n{item.description or ''}",
                f"{item.quantity}",
                f"${item.unit_price:.2f}",
                f"{item.discount_percentage:.2f}%",
                f"{item.tax_percentage:.2f}%",
                f"${item.total_price:.2f}",
            ])
        items_table = Table(items_data, colWidths=[10*mm, 60*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Totals:", styles['Heading2']))
        elements.append(Spacer(1, 6))
        totals_data = [
            ["Subtotal:", f"${invoice.subtotal:.2f}"],
            ["Discount:", f"-${invoice.discount_amount:.2f}"],
            ["Tax:", f"+${invoice.tax_amount:.2f}"],
            ["Total:", f"${invoice.total_amount:.2f}"],
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
        elements.append(Spacer(1, 12))

        payment_data = [
            ["Paid Amount:", f"${invoice.paid_amount:.2f}"],
            ["Balance Due:", f"${invoice.balance_due:.2f}"],
        ]
        payment_table = Table(payment_data, colWidths=[100*mm, 50*mm])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))

        if invoice.notes:
            elements.append(Paragraph("Notes:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(invoice.notes, styles['Normal']))
            elements.append(Spacer(1, 12))

        if invoice.terms_conditions:
            elements.append(Paragraph("Terms & Conditions:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(invoice.terms_conditions, styles['Normal']))
            elements.append(Spacer(1, 12))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your business!", styles['Normal']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))

        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)

        default_recipient = ''
        if invoice.contact_person and invoice.contact_person.email:
            default_recipient = invoice.contact_person.email
        elif invoice.client.email:
            default_recipient = invoice.client.email

        recipient_email = request.POST.get('recipient_email', default_recipient)
        template_id = request.POST.get('template')
        subject = request.POST.get('subject', f'Invoice {invoice.invoice_number}')
        message = request.POST.get('message', '')

        if not recipient_email:
            messages.error(request, 'Recipient email is required.')
            return redirect('invoices:invoice_detail', pk=pk)

        # Use template if selected
        if template_id:
            try:
                template = EmailTemplate.objects.get(pk=template_id, template_type='invoice', is_active=True)
                context = get_email_context(invoice)
                subject = render_template(template.subject, context)
                message = render_template(template.body, context)
            except EmailTemplate.DoesNotExist:
                pass

        pdf_content = self._generate_pdf(invoice)

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
        email.attach(f'invoice_{invoice.invoice_number}.pdf', pdf_content, 'application/pdf')

        try:
            email.send()

            InvoiceHistory.objects.create(
                invoice=invoice,
                action='email_sent',
                performed_by=request.user,
                description=f"Invoice {invoice.invoice_number} sent to {recipient_email}"
            )

            messages.success(request, f'Invoice sent successfully to {recipient_email}.')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')

        return redirect('invoices:invoice_detail', pk=pk)


class InvoiceReminderEmailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.send_invoice_reminder'

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)

        default_recipient = ''
        if invoice.contact_person and invoice.contact_person.email:
            default_recipient = invoice.contact_person.email
        elif invoice.client.email:
            default_recipient = invoice.client.email

        recipient_email = request.POST.get('recipient_email', default_recipient)
        template_id = request.POST.get('template')
        subject = request.POST.get('subject', f'Payment Reminder: Invoice {invoice.invoice_number}')
        message = request.POST.get('message', f'This is a reminder for invoice {invoice.invoice_number} with balance due of ${invoice.balance_due:.2f}. Please make the payment at your earliest convenience.')

        if not recipient_email:
            messages.error(request, 'Recipient email is required.')
            return redirect('invoices:invoice_detail', pk=pk)

        # Use template if selected
        if template_id:
            try:
                template = EmailTemplate.objects.get(pk=template_id, template_type='reminder', is_active=True)
                context = get_email_context(invoice)
                subject = render_template(template.subject, context)
                message = render_template(template.body, context)
            except EmailTemplate.DoesNotExist:
                pass

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

        try:
            email.send()

            InvoiceHistory.objects.create(
                invoice=invoice,
                action='email_sent',
                performed_by=request.user,
                description=f"Payment reminder sent for invoice {invoice.invoice_number} to {recipient_email}"
            )

            messages.success(request, f'Payment reminder sent successfully to {recipient_email}.')
        except Exception as e:
            messages.error(request, f'Failed to send reminder: {str(e)}')

        return redirect('invoices:invoice_detail', pk=pk)


class InvoiceHistoryView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListView):
    model = InvoiceHistory
    template_name = 'invoices/invoice_history.html'
    context_object_name = 'history'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.view_invoicehistory'

    def get_queryset(self):
        self.invoice = get_object_or_404(Invoice, pk=self.kwargs['pk'], is_deleted=False)
        return InvoiceHistory.objects.filter(invoice=self.invoice).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['invoice'] = self.invoice
        return context


class InvoiceConvertView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'invoices.add_invoice'

    def get(self, request, quotation_pk):
        quotation = get_object_or_404(Quotation, pk=quotation_pk, is_deleted=False)
        return redirect(f"{reverse('invoices:invoice_create')}?quotation={quotation.pk}")