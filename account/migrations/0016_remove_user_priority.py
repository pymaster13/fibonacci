# Generated by Django 4.0.4 on 2022-05-11 19:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_user_priority'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='priority',
        ),
    ]