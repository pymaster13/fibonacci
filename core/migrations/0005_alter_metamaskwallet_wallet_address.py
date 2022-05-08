# Generated by Django 4.0.4 on 2022-05-08 20:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_coin_name_alter_coinnetwork_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metamaskwallet',
            name='wallet_address',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.address', verbose_name='Metamask address'),
        ),
    ]
