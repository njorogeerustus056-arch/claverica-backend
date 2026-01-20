from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('kyc', '0001_initial'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql=[
                "-- Migration to document manual fix of user_id type mismatch",
                "-- Changes made:",
                "-- 1. kyc_documents.user_id: VARCHAR(255) → BIGINT",
                "-- 2. kyc_verifications.user_id: VARCHAR(255) → BIGINT",
                "-- This resolves foreign key compatibility issues",
                "SELECT 1;"
            ],
            reverse_sql=[
                "SELECT 1;"
            ],
        )
    ]
