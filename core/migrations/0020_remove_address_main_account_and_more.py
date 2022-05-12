# Generated by Django 4.0.4 on 2022-05-12 21:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_address_coin_address_main_account_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='main_account',
        ),
        migrations.AlterField(
            model_name='adminwallet',
            name='wallet_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.address', verbose_name='Admin wallet address'),
        ),
    ]
