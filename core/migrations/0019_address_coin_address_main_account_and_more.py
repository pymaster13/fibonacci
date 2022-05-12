# Generated by Django 4.0.4 on 2022-05-12 21:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_remove_address_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='coin',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.coin'),
        ),
        migrations.AddField(
            model_name='address',
            name='main_account',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='transaction',
            name='received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='transaction',
            name='referal',
            field=models.BooleanField(default=False),
        ),
    ]
