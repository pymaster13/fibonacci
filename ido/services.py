
from .models import Address, Exchange, Coin, CoinNetwork


def process_ido_data(request_query_dict: dict):

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
        exchange_obj, _ = Exchange.objects.get_or_create(name=exchange)
        exchange = exchange_obj.pk
        tmp_data['exchange'] = exchange

    coin = data.get('coin')
    if coin:
        coin_obj, _ = Coin.objects.get_or_create(name=coin)
        coin = coin_obj.pk
        tmp_data['coin'] = coin

    coin_network = data.get('coin_network')
    if coin_network:
        coin_network_obj, _ = CoinNetwork.objects.get_or_create(
                                                    name=coin_network
                                                    )
        coin_network = coin_network_obj.pk
        tmp_data['coin_network'] = coin_network

    data.update(tmp_data)

    print('result data', data)

    return data
