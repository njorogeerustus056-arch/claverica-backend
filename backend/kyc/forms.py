from django import forms
from django.core.exceptions import ValidationError
from .models import KYCDocument

class KYCDocumentForm(forms.ModelForm):
    """Form for uploading KYC documents"""
    
    # Add accept attribute for file inputs
    id_front_image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text="Front of your ID (National ID, Driver's License, or Passport)"
    )
    
    id_back_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text="Back of your ID (if applicable)"
    )
    
    facial_image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text="Clear selfie or facial photo for verification"
    )
    
    class Meta:
        model = KYCDocument
        fields = ['document_type', 'id_front_image', 'id_back_image', 'facial_image']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        document_type = cleaned_data.get('document_type')
        id_back_image = cleaned_data.get('id_back_image')
        
        # Require back image for certain document types
        if document_type in ['national_id', 'driver_license'] and not id_back_image:
            self.add_error('id_back_image', 
                          'Back image is required for National ID and Driver License')
        
        # Validate file sizes (max 5MB each)
        max_size = 5 * 1024 * 1024  # 5MB
        
        for field_name in ['id_front_image', 'id_back_image', 'facial_image']:
            file = cleaned_data.get(field_name)
            if file and hasattr(file, 'size') and file.size > max_size:
                self.add_error(field_name, 
                             f'File size must be less than 5MB. Current size: {file.size // 1024}KB')
        
        return cleaned_data
