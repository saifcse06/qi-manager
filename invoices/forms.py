from django import forms
from .models import Invoice, InvoiceItem
from clients.models import Client, ClientContactPerson
from quotations.models import Quotation
from products.models import Product


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'contact_person', 'quotation', 'discount_amount', 'tax_amount', 'paid_amount', 'due_date', 'notes', 'terms_conditions']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'contact_person': forms.Select(attrs={'class': 'form-select'}),
            'quotation': forms.Select(attrs={'class': 'form-select'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_deleted=False)
        self.fields['contact_person'].queryset = ClientContactPerson.objects.filter(is_deleted=False, status='active')
        self.fields['quotation'].queryset = Quotation.objects.filter(is_deleted=False, status__in=['approved', 'sent'])
        
        # Make quotation optional
        self.fields['quotation'].required = False
        
        # If editing existing invoice, filter contact persons by client
        if self.instance and self.instance.pk and self.instance.client:
            self.fields['contact_person'].queryset = self.fields['contact_person'].queryset.filter(client=self.instance.client)
    
    def clean(self):
        cleaned_data = super().clean()
        quotation = cleaned_data.get('quotation')
        client = cleaned_data.get('client')
        
        # If quotation is provided but client is not, set client from quotation
        if quotation and not client:
            cleaned_data['client'] = quotation.client
            if quotation.contact_person:
                cleaned_data['contact_person'] = quotation.contact_person
        
        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'discount_percentage', 'tax_percentage']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_deleted=False, status='active')
