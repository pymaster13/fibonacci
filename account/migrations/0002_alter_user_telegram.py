# Generated by Django 4.0.4 on 2022-05-04 22:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='telegram',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='account.tgaccount', verbose_name='Telegram account'),
        ),
    ]
