from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('escrow', '0005_remove_escrow_compliance_reference_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='escrow',
            name='is_released',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='escrow',
            name='release_approved_by_sender',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='escrow',
            name='release_approved_by_receiver',
            field=models.BooleanField(default=False),
        ),
    ]
