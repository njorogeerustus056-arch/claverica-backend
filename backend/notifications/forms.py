# notifications/forms.py
"""
Forms for the notifications application
"""
from django import forms
from .models import Notification, NotificationTemplate


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating/editing notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        widgets = {
            'title_template': forms.TextInput(attrs={'class': 'vTextField'}),
            'message_template': forms.Textarea(attrs={'rows': 3, 'class': 'vLargeTextField'}),
            'action_url_template': forms.TextInput(attrs={'class': 'vTextField'}),
        }
    
    def clean_template_type(self):
        template_type = self.cleaned_data.get('template_type')
        if NotificationTemplate.objects.filter(template_type=template_type).exists():
            instance = getattr(self, 'instance', None)
            if instance and instance.pk:
                # Editing existing template
                pass
            else:
                # Creating new template with existing type
                raise forms.ValidationError(
                    f"A template with type '{template_type}' already exists."
                )
        return template_type


class BulkNotificationForm(forms.Form):
    """Form for sending bulk notifications"""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'selectfilter', 'size': 10})
    )
    notification_type = forms.ChoiceField(
        choices=Notification.NOTIFICATION_TYPES,
        initial='system'
    )
    title = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_LEVELS,
        initial='medium'
    )