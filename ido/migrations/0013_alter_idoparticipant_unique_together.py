# Generated by Django 4.0.4 on 2022-05-10 20:34

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ido', '0012_alter_idoparticipant_queue_place'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='idoparticipant',
            unique_together={('ido', 'user')},
        ),
    ]
