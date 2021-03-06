# Generated by Django 4.0.4 on 2022-05-14 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_alter_address_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminwallet',
            name='balance',
            field=models.DecimalField(blank=True, decimal_places=50, default=0, max_digits=100, null=True, verbose_name='Admin wallet balance'),
        ),
    ]
