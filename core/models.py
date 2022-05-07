from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Address(models.Model):
    """Model of address for metamask or smartcontract"""

    address = models.CharField(max_length=128,
                               unique=True,
                               verbose_name='Address')

    def __str__(self):
        return self.address


class MetamaskWallet(models.Model):
    """Model of Metamask wallet binded to user account"""

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                verbose_name='Metamask owner')
    wallet_address = models.ForeignKey(Address, on_delete=models.CASCADE,
                                       verbose_name='Metamask address')

    def __str__(self):
        return self.wallet_address.address


class Exchange(models.Model):
    """Model of exchange"""

    name = models.CharField(max_length=128,
                            unique=True,
                            verbose_name='Exchange name')

    def __str__(self):
        return self.name


class Coin(models.Model):
    """Model of coin"""

    name = models.CharField(max_length=4,
                            unique=True,
                            verbose_name='Coin abbreviation')

    def __str__(self):
        return self.name


class CoinNetwork(models.Model):
    """Model of coin"""

    name = models.CharField(max_length=4,
                            unique=True,
                            verbose_name='Coin network')

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Model of transaction"""

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
    commission = models.FloatField(null=True,
                                   blank=True,
                                   verbose_name='Transaction commission')
