# Generated by Django 4.0.4 on 2022-05-14 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_alter_user_balance_alter_user_referal_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='hold',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=15),
        ),
    ]