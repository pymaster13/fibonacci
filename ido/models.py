from django.db import models
from django.contrib.auth import get_user_model

from core.models import (Exchange, Coin, Address)


User = get_user_model()


class IDO(models.Model):
    """Model of Initial Dex Offering.
    Fields: type (transcript):
        - name IDO: str
        - description IDO: str
        - general_allocation: float (all money)
        - person_allocation: float (money that user can invest)
        - buy_date: datetime
        - tge: datetime (token generating event)
        - vesting: datetime (where tokens take effect)
        - smartcontract: Address (smart-contract address)
        - exchange: Exchange (reference to exchange)
        - coin: Coin.name (e.g. BTC)
        - commission: float (owner platform commission in percents)
        - telegram_acc: str
        - twitter_acc: str
        - discord_acc: str
        - site: str
        - white_paper: str
        - without_pay: bool
        - charge_manually: bool
        - image: file
    """

    name = models.CharField(max_length=128, verbose_name='Name IDO')
    description = models.TextField(verbose_name='Description IDO')
    general_allocation = models.FloatField(verbose_name='General allocation')
    person_allocation = models.FloatField(verbose_name='Person allocation')
    buy_date = models.DateTimeField(verbose_name='Buy date')
    tge = models.DateTimeField(verbose_name='Token Generating Event')
    vesting = models.CharField(max_length=128, verbose_name='Vesting')
    smartcontract = models.OneToOneField(Address,
                                         null=True,
                                         blank=True,
                                         on_delete=models.CASCADE,
                                         verbose_name='Smartcontract address')
    exchange = models.ForeignKey(Exchange,
                                 null=True, blank=True,
                                 on_delete=models.CASCADE,
                                 verbose_name='Exchange')
    coin = models.ForeignKey(Coin,
                             null=True, blank=True,
                             on_delete=models.CASCADE,
                             verbose_name='Coin')
    commission = models.FloatField(verbose_name='Platform commission, percent')
    telegram_acc = models.CharField(max_length=128,
                                    null=True, blank=True,
                                    verbose_name='Telegram account')
    twitter_acc = models.CharField(max_length=128,
                                   null=True, blank=True,
                                   verbose_name='Twitter account')
    discord_acc = models.CharField(max_length=128,
                                   null=True, blank=True,
                                   verbose_name='Discord account')
    site = models.CharField(max_length=128, null=True, blank=True, verbose_name='Site')
    white_paper = models.CharField(max_length=128,
                                   null=True, blank=True,
                                   verbose_name='White paper')

    without_pay = models.BooleanField(default=False)
    charge_manually = models.BooleanField(default=False)

    image = models.ImageField(upload_to='ido/', null=True, blank=True)
    # image = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "IDO"

    @property
    def count_participants(self):
        return self.general_allocation // self.person_allocation


class IDOParticipant(models.Model):
    """Model of IDO participant.
    Fields: type:
        - ido: IDO
        - user: User
        - priority: str
        - allocation: float
    """

    ido = models.ForeignKey(IDO, default=None, null=True,
                            on_delete=models.CASCADE,
                            verbose_name='IDO')
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='User')
    allocation = models.FloatField(null=True, verbose_name='Allocation')
    date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    refund_allocation = models.FloatField(default=0.0,
                                          verbose_name='Refund allocation')
    income_from_income = models.FloatField(default=0.0,
                                           verbose_name='Income from income')

    class Meta:
        unique_together = ('ido', 'user')


class QueueUser(models.Model):
    """Model of user queue."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='User')
    ido = models.ForeignKey(IDO, default=None, null=True,
                            on_delete=models.CASCADE,
                            verbose_name='IDO')
    number = models.IntegerField(default=0, verbose_name='Number (place)')
    permanent = models.BooleanField(default=False, verbose_name='Permanent')
    date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('ido', 'user')
