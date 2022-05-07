from enum import unique
from django.db import models
from django.contrib.auth import get_user_model

from core.models import (Exchange, Coin, CoinNetwork, Address)


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
        - coin: Coin (e.g. BTC)
        - coin_network: CoinNetwork (e.g. BEP20)
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
    vesting = models.DateTimeField(verbose_name='Vesting')
    smartcontract = models.OneToOneField(Address,
                                         null=True,
                                         on_delete=models.CASCADE,
                                         verbose_name='Smartcontract address')
    exchange = models.ForeignKey(Exchange,
                                 on_delete=models.CASCADE,
                                 verbose_name='Exchange')
    coin = models.ForeignKey(Coin,
                             on_delete=models.CASCADE,
                             verbose_name='Coin')
    coin_network = models.ForeignKey(CoinNetwork,
                                     on_delete=models.CASCADE,
                                     verbose_name='Network')
    commission = models.FloatField(verbose_name='Platform commission, percent')
    telegram_acc = models.CharField(max_length=128,
                                    null=True,
                                    verbose_name='Telegram account')
    twitter_acc = models.CharField(max_length=128,
                                   null=True,
                                   verbose_name='Twitter account')
    discord_acc = models.CharField(max_length=128,
                                   null=True,
                                   verbose_name='Discord account')
    site = models.CharField(max_length=128, null=True, verbose_name='Site')
    white_paper = models.CharField(max_length=128,
                                   null=True,
                                   verbose_name='White paper')

    without_pay = models.BooleanField(default=False)
    charge_manually = models.BooleanField(default=False)

    image = models.ImageField(upload_to='ido/', null=True)

    class Meta:
        verbose_name_plural = "IDO"


class UserOutOrder(models.Model):
    """Model of users thar out of order (IDO.without_pay=True).
    Fields: type (transcript):
        - ido: IDO
        - user: User
        - allocation: float
    """

    ido = models.ForeignKey(IDO,
                            on_delete=models.SET_NULL,
                            null=True,
                            verbose_name='IDO')
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='User')
    allocation = models.FloatField(verbose_name='Allocation')

    class Meta:
        verbose_name_plural = "Users out order"


class ManuallyCharge(models.Model):
    """Model of manually charges of coins (IDO.without_pay=True).
    Fields: type (transcript):
        - ido: IDO
        - amount: float
        - coin: str
    """

    ido = models.ForeignKey(IDO,
                            on_delete=models.CASCADE,
                            verbose_name='IDO')
    amount = models.FloatField(verbose_name='Amount')
    coin = models.ForeignKey(Coin,
                             on_delete=models.CASCADE,
                             verbose_name='Coin')


class IDOParticipant(models.Model):
    """Model of IDO participant.
    Fields: type:
        - ido: IDO
        - user: User
        - priority: str
    """

    ido = models.ForeignKey(IDO, default=None, null=True,
                            on_delete=models.CASCADE,
                            verbose_name='IDO')
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='User')
    priority = models.IntegerField(default=0, verbose_name='Priority')
    allocation = models.FloatField(null=True, verbose_name='Allocation')
