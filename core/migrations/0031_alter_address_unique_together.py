# Generated by Django 4.0.4 on 2022-05-14 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_alter_transaction_commission'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='address',
            unique_together={('address', 'owner_admin')},
        ),
    ]