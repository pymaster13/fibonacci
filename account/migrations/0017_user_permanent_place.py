# Generated by Django 4.0.4 on 2022-05-11 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0016_remove_user_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='permanent_place',
            field=models.IntegerField(null=True),
        ),
    ]
