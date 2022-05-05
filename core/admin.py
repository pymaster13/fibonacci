from django.contrib import admin

from .models import MetamaskWallet


@admin.register(MetamaskWallet)
class MetamaskWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_address')
