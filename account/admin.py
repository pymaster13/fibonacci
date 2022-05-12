from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import TgAccount, TgCode, GoogleAuth


User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        ('Personal info', {'fields': ('email', 'telegram',
                                      'first_name', 'last_name', 'inviter',
                                      'line', 'is_active', 'status', 'permanent_place',
                                      'is_superuser', 'can_invite', 'balance', 'hold',
                                      'is_staff')}),
        ('Password info', {'fields': ('password',)}),
        ('Groups, permissions', {
            'fields': ('groups', 'user_permissions'),
        })
        )

    add_fieldsets = (
        ('Create', {
            'classes': ('wide',),
            'fields': ('email', 'telegram', 'password1', 'password2'),
        }),
        )

    list_display = ('id', 'email', 'telegram', 'first_name', 'last_name', 'line',
                    'is_active', 'is_staff', 'invite_code', 'can_invite',
                    'status')
    search_fields = ('email', 'telegram')
    ordering = ('email', 'line', 'telegram')


@admin.register(TgAccount)
class TgAccountAdmin(admin.ModelAdmin):
    list_display = ('tg_nickname', 'is_confirmed')


@admin.register(TgCode)
class TgCodeAdmin(admin.ModelAdmin):
    list_display = ('tg_account', 'code', 'created')


@admin.register(GoogleAuth)
class GoogleAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'is_installed')
