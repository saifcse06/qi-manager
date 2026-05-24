from django import forms
from .models import Quotation, QuotationItem
from clients.models import Client, ClientContactPerson
from products.models import Product


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'client', 'contact_person', 'status', 
            'discount_amount', 'tax_amount', 'notes', 'terms_conditions'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'contact_person': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter contact persons based on selected client
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['contact_person'].queryset = ClientContactPerson.objects.filter(
                    client_id=client_id, is_deleted=False
                )
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to queryset
        elif self.instance.pk:
            self.fields['contact_person'].queryset = ClientContactPerson.objects.filter(
                client=self.instance.client, is_deleted=False
            )
        else:
            self.fields['contact_person'].queryset = ClientContactPerson.objects.none()


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            'product', 'description', 'quantity', 
            'unit_price', 'discount_percentage', 'tax_percentage'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active products
        self.fields['product'].queryset = Product.objects.filter(status='active', is_deleted=False)