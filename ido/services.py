from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import Address, Exchange, Coin, IDO
from .exceptions import (ExchangeAddError, SmartcontractAddError,
                         CoinAddError)
from account.exceptions import EmailValidationError, UserDoesNotExists

User = get_user_model()


def process_ido_data(request_query_dict: dict):

    if not request_query_dict:
        return

    data = dict(request_query_dict)
    print('request data', data)

    tmp_data = {}

    smartcontract = data.get('smartcontract')
    if smartcontract:
        smartcontract_obj, _ = Address.objects.get_or_create(
                                            address=smartcontract
                                            )
        if IDO.objects.filter(smartcontract=smartcontract_obj):
            raise SmartcontractAddError("Этот адрес смартконтракта уже зарегистрирован.")

        smartcontract = smartcontract_obj.pk
        tmp_data['smartcontract'] = smartcontract

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

    data.update(tmp_data)

    print('result data', data)

    return data, users_obj
