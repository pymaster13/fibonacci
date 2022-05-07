from django.contrib import admin

from .models import (IDO, UserOutOrder,
                     ManuallyCharge, IDOParticipant)


@admin.register(IDO)
class IDOAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'description', 'person_allocation')


@admin.register(UserOutOrder)
class UserOutOrderAdmin(admin.ModelAdmin):
    list_display = ('ido', 'user', 'allocation')


@admin.register(ManuallyCharge)
class ManuallyChargeAdmin(admin.ModelAdmin):
    list_display = ('ido', 'amount', 'coin')


@admin.register(IDOParticipant)
class IDOParticipantAdmin(admin.ModelAdmin):
    list_display = ('ido', 'user', 'priority')
