import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def add_complianceprofile(apps, schema_editor):
    pass  # We'll use manual SQL

class Migration(migrations.Migration):
    dependencies = [
        ('compliance_module', '0001_initial_fixed'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    
    operations = [
        migrations.CreateModel(
            name='ComplianceProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kyc_status', models.CharField(choices=[('pending', 'Pending'), ('in_review', 'In Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low', max_length=20)),
                ('last_kyc_date', models.DateTimeField(blank=True, null=True)),
                ('next_kyc_review', models.DateTimeField(blank=True, null=True)),
                ('restrictions', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compliance_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

