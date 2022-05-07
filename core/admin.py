from django.contrib import admin

from .models import (MetamaskWallet, Coin, CoinNetwork,
                     Exchange, Address, Transaction)


@admin.register(MetamaskWallet)
class MetamaskWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_address')


@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


@admin.register(CoinNetwork)
class CoinNetworkAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('address',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('address_from', 'address_to',
                    'coin', 'amount', 'commission')
