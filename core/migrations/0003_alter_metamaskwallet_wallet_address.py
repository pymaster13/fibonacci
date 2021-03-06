# Generated by Django 4.0.4 on 2022-05-06 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_address_coin_coinnetwork_exchange_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metamaskwallet',
            name='wallet_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.address', verbose_name='Metamask address'),
        ),
    ]
