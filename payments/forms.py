from django import forms
from .models import Payment, PaymentRefund
from invoices.models import Invoice
from settings_app.models import PaymentMethod


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'payment_method', 'amount', 'payment_date', 'payment_method_name', 'reference_number', 'remarks', 'status']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].queryset = Invoice.objects.filter(is_deleted=False)
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.payment_method:
            self.fields['payment_method_name'].initial = self.instance.payment_method.name

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        if payment_method and not cleaned_data.get('payment_method_name'):
            cleaned_data['payment_method_name'] = payment_method.name
        return cleaned_data
