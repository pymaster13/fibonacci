# Generated by Django 4.0.4 on 2022-05-13 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_alter_adminwallet_decimal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminwallet',
            name='balance',
            field=models.DecimalField(blank=True, decimal_places=50, max_digits=100, null=True, verbose_name='Admin wallet balance'),
        ),
    ]
