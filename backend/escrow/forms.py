from django import forms
from .models import Escrow

class EscrowForm(forms.ModelForm):
    class Meta:
        model = Escrow
        fields = [
            'sender_id', 'sender_name', 'receiver_id', 'receiver_name',
            'amount', 'currency', 'title', 'description',
            'terms_and_conditions', 'expected_release_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 3}),
            'expected_release_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }