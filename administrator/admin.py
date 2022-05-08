from django.contrib import admin

from .models import VIPUser


@admin.register(VIPUser)
class VIPUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'referal_profit')