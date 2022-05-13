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
    cost_in_busd = models.FloatField(null=True, blank=True,
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
        unique_together = ('address', 'coin')

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
    balance = models.DecimalField(null=True, blank=True, max_digits=100,
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
    commission = models.DecimalField(null=True, blank=True, max_digits=100,
                                     decimal_places=50,
                                     verbose_name='Transaction commission')
    referal = models.BooleanField(default=False)
    received = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True)


class AccountBalance(models.Model):
    """Model of account balance."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Owner account',
                             related_name='owner_account')
    from_user = models.ForeignKey(User,
                                  null=True,
                                  blank=True,
                                  on_delete=models.CASCADE,
                                  verbose_name='Invited account',
                                  related_name='invited_account')
    coin = models.ForeignKey(Coin,
                             on_delete=models.CASCADE,
                             verbose_name='Transaction coin')
    avaliable = models.FloatField(default=0.0, verbose_name='Available coins')
    received = models.FloatField(default=0.0, verbose_name='Received coins')
    refund_allocation = models.FloatField(default=0.0,
                                          verbose_name='Refund allocation')
    income_from_income = models.FloatField(default=0.0,
                                           verbose_name='Income from income')

    date = models.DateTimeField(auto_now_add=True)
