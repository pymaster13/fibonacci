# Generated by Django 4.0.4 on 2022-05-09 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_adminwallet_wallet_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminwallet',
            name='balance',
            field=models.FloatField(default=0, verbose_name='Admin wallet balance'),
        ),
        migrations.AddField(
            model_name='metamaskwallet',
            name='balance',
            field=models.FloatField(default=0, verbose_name='Metamask wallet balance'),
        ),
    ]
