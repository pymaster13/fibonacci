
from .models import Address, Exchange, Coin
from .exceptions import ExchangeAddError


def process_ido_data(request_query_dict: dict):

    if not request_query_dict:
        return

    data = dict(request_query_dict.dict())
    print('request data', data)

    tmp_data = {}

    smartcontract = data.get('smartcontract')
    if smartcontract:
        smartcontract_obj, _ = Address.objects.get_or_create(
                                            address=smartcontract
                                            )
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
        raise ExchangeAddError('Указаны неверные данные о монете.')

    data.update(tmp_data)

    print('result data', data)

    return data
