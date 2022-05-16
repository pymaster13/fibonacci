from django.contrib.auth import get_user_model
from django.db import models
from config.settings import AUTH_USER_MODEL

# User = get_user_model()
User = AUTH_USER_MODEL


class Coin(models.Model):
    """Model of coin."""

    name = models.CharField(max_length=4,
                            unique=True,
                            verbose_name='Coin abbreviation')
    network = models.CharField(max_length=128,
                               unique=True,
                               verbose_name='Coin network')
    cost_in_busd = models.DecimalField(null=True, blank=True, max_digits=100,
                                       decimal_places=50,
                                       verbose_name='BUSD cost')

    def __str__(self):
        return self.name


class Address(models.Model):
    """Model of address for metamask or smartcontract."""

    address = models.CharField(max_length=128,
                               verbose_name='Address')
    coin = models.ForeignKey(Coin,
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True)
    owner_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('address', 'owner_admin')

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

    wallet_address = models.ForeignKey(Address, on_delete=models.CASCADE,
                                       verbose_name='Admin wallet address')
    balance = models.DecimalField(default=0, null=True, blank=True, max_digits=100,
                                  decimal_places=50, verbose_name='Admin wallet balance')
    decimal = models.IntegerField(default=0, verbose_name='Admin wallet decimal')

    def __str__(self):
        return self.wallet_address.address


class Exchange(models.Model):
    """Model of exchange."""

    reference = models.CharField(max_length=128,
                                 unique=True,
                                 verbose_name='Exchange reference')

    def __str__(self):
        return self.reference


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
    amount = models.DecimalField(null=True, blank=True, max_digits=100,
                                 decimal_places=50,
                                 verbose_name='Transaction amount (volume)')
    commission = models.BooleanField(default=False)
    referal = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    fill_up = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True)
