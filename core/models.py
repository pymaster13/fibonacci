from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Address(models.Model):
    """Model of address for metamask or smartcontract."""

    address = models.CharField(max_length=128,
                               unique=True,
                               verbose_name='Address')

    def __str__(self):
        return self.address


class MetamaskWallet(models.Model):
    """Model of Metamask wallet binded to user account."""

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                verbose_name='Metamask owner')
    wallet_address = models.ForeignKey(Address, on_delete=models.CASCADE,
                                       verbose_name='Metamask address')

    def __str__(self):
        return self.wallet_address.address


class AdminWallet(models.Model):
    """Model of Admin metamask wallet."""

    wallet_address = models.OneToOneField(Address, on_delete=models.CASCADE,
                                          verbose_name='Admin wallet address')
    balance = models.FloatField(default=0, verbose_name='Admin wallet balance')

    def __str__(self):
        return self.wallet_address.address


class Exchange(models.Model):
    """Model of exchange."""

    reference = models.CharField(max_length=128,
                                 unique=True,
                                 verbose_name='Exchange reference')

    def __str__(self):
        return self.reference


class Coin(models.Model):
    """Model of coin."""

    name = models.CharField(max_length=4,
                            unique=True,
                            verbose_name='Coin abbreviation')
    network = models.CharField(max_length=128,
                               unique=True,
                               verbose_name='Coin network')

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Model of transaction."""

    address_from = models.ForeignKey(Address,
                                     on_delete=models.CASCADE,
                                     verbose_name='Transaction source',
                                     related_name='transaction_address_from')
    address_to = models.ForeignKey(Address,
                                   on_delete=models.CASCADE,
                                   verbose_name='Transaction receiver',
                                   related_name='transaction_address_to')
    coin = models.ForeignKey(Coin,
                             on_delete=models.CASCADE,
                             verbose_name='Transaction coin')
    amount = models.FloatField(verbose_name='Transaction amount (volume)')
    commission = models.FloatField(default=0,
                                   verbose_name='Transaction commission')
    date = models.DateTimeField(auto_now_add=True)
