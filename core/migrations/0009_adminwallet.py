# Generated by Django 4.0.4 on 2022-05-09 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_coin_network_alter_exchange_reference_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallet_address', models.CharField(max_length=128, unique=True, verbose_name='Admin metamask wallet')),
            ],
        ),
    ]
