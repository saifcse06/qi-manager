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
from .models import Quotation, QuotationItem, QuotationHistory
from clients.models import Client, ClientContactPerson
from products.models import Product
from .forms import QuotationForm, QuotationItemForm
from datetime import datetime


def _sidebar_context():
    return {
        'quotation_count': Quotation.objects.filter(is_deleted=False).count(),
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


# Quotation Views
class QuotationListView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListViewMixin, ListView):
    model = Quotation
    template_name = 'quotations/quotation_list.html'
    context_object_name = 'quotations'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.view_quotation'

    def get_queryset(self):
        queryset = Quotation.objects.filter(is_deleted=False).order_by('-created_at')
        search_query = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        client_filter = self.request.GET.get('client')
        if search_query:
            queryset = queryset.filter(
                Q(quotation_number__icontains=search_query) |
                Q(client__company_name__icontains=search_query) |
                Q(contact_person__person_name__icontains=search_query)
            )
        if status_filter in dict(Quotation.STATUS_CHOICES):
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


class QuotationCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Quotation
    form_class = QuotationForm
    template_name = 'quotations/quotation_form.html'
    success_url = reverse_lazy('quotations:quotation_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.add_quotation'

    def form_valid(self, form):
        # Generate quotation number
        from django.utils.crypto import get_random_string
        import datetime
        
        today = datetime.date.today()
        random_str = get_random_string(length=6).upper()
        quotation_number = f"QT-{today.strftime('%Y%m%d')}-{random_str}"
        
        form.instance.quotation_number = quotation_number
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        response = super().form_valid(form)
        
        # Create history entry
        QuotationHistory.objects.create(
            quotation=self.object,
            action='create',
            performed_by=self.request.user,
            description=f"Quotation {self.object.quotation_number} created"
        )
        
        messages.success(self.request, 'Quotation created successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class QuotationUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Quotation
    form_class = QuotationForm
    template_name = 'quotations/quotation_form.html'
    success_url = reverse_lazy('quotations:quotation_list')
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.change_quotation'

    def get_queryset(self):
        return Quotation.objects.filter(is_deleted=False)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # Track changes for history
        if self.object.pk:
            old_status = self.object.status
            old_notes = self.object.notes
            old_terms = self.object.terms_conditions
            
            response = super().form_valid(form)
            
            # Create history entries for changes
            changes = []
            if old_status != self.object.status:
                changes.append(f"Status changed from {dict(Quotation.STATUS_CHOICES)[old_status]} to {dict(Quotation.STATUS_CHOICES)[self.object.status]}")
            if old_notes != self.object.notes:
                changes.append("Notes updated")
            if old_terms != self.object.terms_conditions:
                changes.append("Terms and Conditions updated")
                
            if changes:
                QuotationHistory.objects.create(
                    quotation=self.object,
                    action='update',
                    performed_by=self.request.user,
                    description="; ".join(changes)
                )
        else:
            response = super().form_valid(form)
            
        messages.success(self.request, 'Quotation updated successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class QuotationDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Quotation
    template_name = 'quotations/quotation_confirm_delete.html'
    success_url = reverse_lazy('quotations:quotation_list')
    required_roles = ['Super Admin']
    required_permission = 'quotations.delete_quotation'

    def get_queryset(self):
        return Quotation.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        
        # Create history entry
        QuotationHistory.objects.create(
            quotation=self.object,
            action='delete',
            performed_by=self.request.user,
            description=f"Quotation {self.object.quotation_number} soft deleted"
        )
        
        messages.success(self.request, 'Quotation deleted successfully.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        return context


class QuotationDetailView(DetailView):
    model = Quotation
    template_name = 'quotations/quotation_detail.html'
    context_object_name = 'quotation'

    def get_queryset(self):
        return Quotation.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['items'] = self.object.items.all()
        context['history'] = self.object.history.all()[:10]  # Last 10 history entries
        return context


# Quotation Item Views
class QuotationItemCreateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    model = QuotationItem
    form_class = QuotationItemForm
    template_name = 'quotations/quotationitem_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.add_quotationitem'

    def form_valid(self, form):
        form.instance.quotation_id = self.kwargs['quotation_pk']
        response = super().form_valid(form)
        
        # Create history entry
        quotation = self.object.quotation
        QuotationHistory.objects.create(
            quotation=quotation,
            action='update',
            performed_by=self.request.user,
            description=f"Item {self.object.product.name} added to quotation"
        )
        
        messages.success(self.request, 'Item added successfully.')
        return response

    def get_success_url(self):
        return reverse('quotations:quotation_detail', kwargs={'pk': self.kwargs['quotation_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['quotation'] = get_object_or_404(Quotation, pk=self.kwargs['quotation_pk'])
        return context


class QuotationItemUpdateView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = QuotationItem
    form_class = QuotationItemForm
    template_name = 'quotations/quotationitem_form.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.change_quotationitem'

    def get_queryset(self):
        return QuotationItem.objects.filter(quotation__is_deleted=False)

    def form_valid(self, form):
        self.object = form.save()
        
        # Create history entry
        quotation = self.object.quotation
        QuotationHistory.objects.create(
            quotation=quotation,
            action='update',
            performed_by=self.request.user,
            description=f"Item {self.object.product.name} updated in quotation"
        )
        
        messages.success(self.request, 'Item updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('quotations:quotation_detail', kwargs={'pk': self.object.quotation.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['quotation'] = self.object.quotation
        return context


class QuotationItemDeleteView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = QuotationItem
    template_name = 'quotations/quotationitem_confirm_delete.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.delete_quotationitem'

    def get_queryset(self):
        return QuotationItem.objects.filter(quotation__is_deleted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        quotation = self.object.quotation
        item_description = f"{self.object.product.name} x {self.object.quantity}"
        
        self.object.delete()
        
        # Create history entry
        QuotationHistory.objects.create(
            quotation=quotation,
            action='update',
            performed_by=self.request.user,
            description=f"Item {item_description} removed from quotation"
        )
        
        messages.success(self.request, 'Item deleted successfully.')
        return redirect('quotations:quotation_detail', pk=quotation.pk)

    def get_success_url(self):
        return reverse('quotations:quotation_detail', kwargs={'pk': self.object.quotation.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['quotation'] = self.object.quotation
        return context


# PDF and Email Views
class QuotationPDFView(DetailView):
    model = Quotation
    template_name = 'quotations/quotation_pdf.html'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.view_quotation'

    def get_queryset(self):
        return Quotation.objects.filter(is_deleted=False)

    def render_to_response(self, context, **response_kwargs):
        # Generate PDF using ReportLab
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
        
        # Company logo (if available)
        # We'll skip logo for now, but you can add it from settings
        # if hasattr(settings, 'company_logo') and settings.company_logo:
        #     logo = Image(settings.company_logo.path, width=40*mm, height=20*mm)
        #     elements.append(logo)
        #     elements.append(Spacer(1, 12))
        
        # Title
        elements.append(Paragraph("QUOTATION", title_style))
        elements.append(Spacer(1, 12))
        
        # Quotation number and date
        quotation = self.object
        data = [
            ["Quotation Number:", quotation.quotation_number],
            ["Date:", quotation.created_at.strftime("%B %d, %Y")],
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
            [quotation.client.company_name],
            [quotation.client.address or ''],
            [f"Email: {quotation.client.email or ''}"],
            [f"Phone: {quotation.client.phone or ''}"],
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
        for i, item in enumerate(quotation.items.all(), start=1):
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
            ["Subtotal:", f"${quotation.subtotal:.2f}"],
            ["Discount:", f"-${quotation.discount_amount:.2f}"],
            ["Tax:", f"+${quotation.tax_amount:.2f}"],
            ["Total:", f"${quotation.total_amount:.2f}"],
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
        
        # Notes
        if quotation.notes:
            elements.append(Paragraph("Notes:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(quotation.notes, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Terms & Conditions
        if quotation.terms_conditions:
            elements.append(Paragraph("Terms & Conditions:", styles['Heading2']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(quotation.terms_conditions, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your business!", styles['Normal']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))
        
        doc.build(elements)
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quotation_{quotation.quotation_number}.pdf"'
        return response


class QuotationEmailView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, View):
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.send_quotation'

    def post(self, request, pk):
        quotation = get_object_or_404(Quotation, pk=pk, is_deleted=False)
        
        # Get email details from form
        recipient_email = request.POST.get('recipient_email')
        subject = request.POST.get('subject', f'Quotation {quotation.quotation_number}')
        message = request.POST.get('message', '')
        
        if not recipient_email:
            messages.error(request, 'Recipient email is required.')
            return redirect('quotations:quotation_detail', pk=pk)
        
        # Create email
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        
        # Attach PDF (in a real implementation, we would generate and attach PDF)
        # For now, we'll just send a placeholder
        
        try:
            email.send()
            
            # Create history entry
            QuotationHistory.objects.create(
                quotation=quotation,
                action='email_sent',
                performed_by=request.user,
                description=f"Quotation {quotation.quotation_number} sent to {recipient_email}"
            )
            
            # Update status if it's still in draft
            if quotation.status == 'draft':
                quotation.status = 'sent'
                quotation.updated_by = request.user
                quotation.save()
                
                # Create history entry for status change
                QuotationHistory.objects.create(
                    quotation=quotation,
                    action='status_change',
                    performed_by=request.user,
                    description=f"Status changed from Draft to Sent"
                )
            
            messages.success(request, f'Quotation sent successfully to {recipient_email}.')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')
        
        return redirect('quotations:quotation_detail', pk=pk)


class QuotationHistoryView(LoginRequiredMixin, RoleRequiredMixin, PermissionRequiredMixin, ListView):
    model = QuotationHistory
    template_name = 'quotations/quotation_history.html'
    context_object_name = 'history'
    required_roles = ['Super Admin', 'Admin']
    required_permission = 'quotations.view_quotationhistory'

    def get_queryset(self):
        self.quotation = get_object_or_404(Quotation, pk=self.kwargs['pk'], is_deleted=False)
        return QuotationHistory.objects.filter(quotation=self.quotation).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_sidebar_context())
        context['quotation'] = self.quotation
        return context