# Generated by Django 4.0.4 on 2022-05-05 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ido', '0003_alter_useroutorder_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ido',
            name='image',
            field=models.ImageField(null=True, upload_to='ido/'),
        ),
    ]
