# Generated by Django 4.0.4 on 2022-05-07 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ido', '0007_alter_manuallycharge_ido_alter_useroutorder_ido_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='idoparticipant',
            name='allocation',
            field=models.FloatField(null=True, verbose_name='Allocation'),
        ),
    ]