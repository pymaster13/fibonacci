from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import Address, Exchange, Coin, IDO
from .exceptions import (ExchangeAddError, SmartcontractAddError,
                         CoinAddError)
from account.exceptions import EmailValidationError, UserDoesNotExists
from core.models import MetamaskWallet, Transaction
from ido.models import IDOParticipant
from core.models import AdminWallet
from core.services import get_main_wallet


User = get_user_model()


def process_ido_data(request_query_dict: dict):

    if not request_query_dict:
        return

    data = dict(request_query_dict)

    tmp_data = {}

    exchange = data.get('exchange')
    if exchange:
        exchange_obj, _ = Exchange.objects.get_or_create(reference=exchange)
        tmp_data['exchange'] = exchange_obj.pk

    try:
        coin = data.get('coin')
        coin_network = data.get('coin_network')
        if coin and coin_network:
            coin_obj, _ = Coin.objects.get_or_create(name=coin,
                                                     network=coin_network)
            tmp_data['coin'] = coin_obj.pk
    except Exception:
        raise CoinAddError('Указаны неверные данные о монете.')

    smartcontract = data.get('smartcontract')
    if smartcontract:
        smartcontract_obj, _ = Address.objects.get_or_create(
                                            address=smartcontract,
                                            coin=coin_obj
                                            )
        if IDO.objects.filter(smartcontract=smartcontract_obj):
            raise SmartcontractAddError("Этот адрес смартконтракта уже зарегистрирован.")

        smartcontract = smartcontract_obj.pk
        tmp_data['smartcontract'] = smartcontract

    users_obj = []
    users = data.pop('users', [])
    if users:
        for email in users:
            try:
                validate_email(email)
            except ValidationError:
                raise EmailValidationError('Введите корректный почтовый ящик.')
            try:
                user = User.objects.get(email=email)
            except Exception:
                raise UserDoesNotExists(
                    'Пользователя с такой электронной почтой не существует.'
                    )
            users_obj.append(user)

    allocations = data.pop('allocations', [])
    data.update(tmp_data)

    return data, users_obj, allocations


def fill_admin_wallet(user, amount: Decimal):
    admin_wallet = get_main_wallet()
    metamask_from = MetamaskWallet.objects.get(user=user)
    coin, _ = Coin.objects.get_or_create(name='BUSD',
                                         network='BEP20')
    Transaction.objects.create(
                    address_from=metamask_from.wallet_address,
                    address_to=admin_wallet.wallet_address,
                    coin=coin,
                    amount=amount,
                    commission=True
                    )

def takeoff_admin_wallet(amount):
    admin_wallet = get_main_wallet()
    admin_wallet.balance -= Decimal(amount)
    admin_wallet.save()


def realize_ido_part_referal(user: User, referal: Decimal):
    coin, _ = Coin.objects.get_or_create(name='BUSD',
                                         network='BEP20')
    metamask_from = MetamaskWallet.objects.get(user=user)
    metamask_to = MetamaskWallet.objects.get(user=user.inviter)
    transaction = Transaction.objects.create(
                    address_from=metamask_from.wallet_address,
                    address_to=metamask_to.wallet_address,
                    coin=coin,
                    amount=Decimal(referal),
                    referal=True
    )
    user.inviter.referal_balance += transaction.amount
    user.inviter.save()


def decline_ido_part_referal(user: User, referal, date):
    user.inviter.balance -= Decimal(referal)
    user.inviter.save()
    coin, _ = Coin.objects.get_or_create(name='BUSD',
                                         network='BEP20')
    metamask_from = MetamaskWallet.objects.get(user=user)
    metamask_to = MetamaskWallet.objects.get(user=user.inviter)
    for t in Transaction.objects.filter(
                    address_from=metamask_from.wallet_address,
                    address_to=metamask_to.wallet_address,
                    coin=coin):
        diff = t.date - date
        if diff.total_seconds() < 0.5:
            t.delete()
            break


def participate_ido(user: User, ido: IDO, allocation, wo_pay=False):
    allocation = float(allocation)
    participant, _ = IDOParticipant.objects.get_or_create(
                                        user=user,
                                        ido=ido)
    participant.allocation = allocation
    participant.save()
    if not wo_pay:
        if user.hold:
            user.balance -= Decimal(allocation)
        else:
            user.balance -= Decimal(1.3 * allocation)
    user.can_invite = True
    user.status = 'P'
    user.save()


def count_referal_hold(user: User, allocation):
    if user.hold:
        if allocation > user.hold:
            referal = (Decimal(allocation) - user.hold) * Decimal(0.05)
            user.hold = Decimal(0)
        else:
            referal = Decimal(0)
            user.hold -= Decimal(allocation)
    else:
        referal = Decimal(allocation) * Decimal(0.05)

    user.save()
    return referal


def delete_participant(participant, allocation):
    referal = count_referal_hold(participant.user,
                                 allocation)
    referal = (Decimal(allocation) - user.hold) * Decimal(0.05)
    takeoff_admin_wallet(Decimal(allocation) * Decimal(0.3))
    if referal and participant.user.inviter:
        decline_ido_part_referal(participant.user,
                                 referal, participant.date)
    participant.user.balance += Decimal(1.3) * Decimal(allocation)
    participant.delete()
