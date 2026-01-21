from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('compliance', '0003_alter_auditlog_options_alter_check_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='user_id',
            field=models.CharField(default='0', max_length=255),
        ),
        migrations.AlterField(
            model_name='check',
            name='risk_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='check',
            name='matches_found',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='check',
            name='verification_id',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
