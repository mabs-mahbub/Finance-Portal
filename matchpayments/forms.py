from django.forms import ModelForm, widgets
from django import forms
from .models import PaymentRequest, PaymentsData

class MatchForm(forms.ModelForm):
    class Meta:
        model = PaymentsData
        fields = '__all__'
        widgets = {
            'match': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'players': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'playerspaid': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'datespent': forms.DateInput(attrs={'class': 'form-control'})
        }
        