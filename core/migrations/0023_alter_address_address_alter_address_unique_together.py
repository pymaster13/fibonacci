# Generated by Django 4.0.4 on 2022-05-12 22:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_adminwallet_decimal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address',
            field=models.CharField(max_length=128, verbose_name='Address'),
        ),
        migrations.AlterUniqueTogether(
            name='address',
            unique_together={('address', 'coin')},
        ),
    ]
