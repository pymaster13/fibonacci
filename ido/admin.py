from django.contrib import admin

from .models import (IDO, IDOParticipant, QueueUser)


@admin.register(IDO)
class IDOAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'description', 'person_allocation')


@admin.register(IDOParticipant)
class IDOParticipantAdmin(admin.ModelAdmin):
    list_display = ('ido', 'user', 'allocation', 'date')


@admin.register(QueueUser)
class QueueUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'ido', 'user', 'number', 'permanent', 'date')
