# Generated by Django 4.0.4 on 2022-05-14 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_coin_cost_in_busd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coin',
            name='cost_in_busd',
            field=models.DecimalField(blank=True, decimal_places=50, max_digits=100, null=True, verbose_name='BUSD cost'),
        ),
    ]
