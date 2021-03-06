# Generated by Django 4.0.4 on 2022-05-11 21:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ido', '0017_rename_queueusers_queueuser'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='queueuser',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='queueuser',
            name='ido',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='ido.ido', verbose_name='IDO'),
        ),
        migrations.AlterUniqueTogether(
            name='queueuser',
            unique_together={('ido', 'user', 'number', 'permanent')},
        ),
    ]
