from decimal import Decimal, getcontext
import os
from pprint import pprint
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import sys

import dramatiq
from core.models import Coin

from core.services import (get_custom_admin_wallets,
                           divide, fill_admin_custom_wallet, distribute_tokens)

from config.settings import COINMARKETCAP_API_KEY, ETHERSCAN_API

from pycoingecko import CoinGeckoAPI
# from pythonpancakes import PancakeSwapAPI
import defi.defi_tools as dft
from decimal import getcontext, Decimal
import time

from ido.models import IDO


"""
Run dramatiq workers - "python3 manage.py rundramatiq"
"""

# contract = '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
# contract2= '0x57d90b64a1a57749b0f932f1a3395792e12e7055'
# account = '0x4e83362442b8d1bec281594cea3050c8eb01311c'
# account2 = '0xe04f27eb70e025b78871a2ad7eabe85e61212761'


@dramatiq.actor
def scan_admin_wallets():
    """Regular task for scanning admin_wallets"""

    print('FUCK')

    admin_wallets = get_custom_admin_wallets()

    for wallet in admin_wallets:
        print(1)
        ido = IDO.objects.get(coin=wallet.wallet_address.coin)
        smart = ido.smartcontract
        address = wallet.wallet_address.address
        print(2)
        url = f'https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={smart}&address={address}&tag=latest&apikey={ETHERSCAN_API}'
        response = requests.get(url)
        data = response.json()
        print(3)
        # {'status': '1', 'message': 'OK', 'result': '135499'}
        if data.get('message') == 'OK':
            getcontext().prec = wallet.decimal

            print(data.get('result'))
            print(wallet.decimal)

            tokens = divide(data.get('result'), wallet.decimal)
            print(tokens)

            # wallet.balance - in db
            # tokens - real balance on admin wallet
            print(repr(tokens - wallet.balance))

            if wallet.balance < tokens:
                getcontext().prec = wallet.decimal
                print(repr(tokens))
                print(repr(wallet.balance))
                diff = Decimal(tokens) - Decimal(wallet.balance)

                transaction = fill_admin_custom_wallet(wallet, smart, diff)
                distribute_tokens(wallet, smart, transaction.amount)

                wallet.balance = tokens
                wallet.save()


@dramatiq.actor
def retreive_coins_cost():
    busd = Coin.objects.get(name='BUSD')
    coins = Coin.objects.all().exclude(name='BUSD')
    getcontext().prec = 50
    try:
        if busd:
            cg = CoinGeckoAPI()
            coins_list = cg.get_coins_list()
            print('BUSD')

            for cg_coin in coins_list:
                if cg_coin['symbol'] == busd.name.lower():
                    coin_id = cg_coin['id']
                    try:
                        busd_price = cg.get_price(ids=coin_id,
                                                  vs_currencies='usd')
                    except Exception as e:
                        print(e)
                    else:
                        busd.cost_in_busd = Decimal(busd_price[coin_id]['usd'])
                        busd.save()
                        print(busd.cost_in_busd)

            if coins:
                for coin in coins:
                    print(coin.name)
                    # {'id': 'zyx', 'symbol': 'zyx', 'name': 'ZYX'}
                    for cg_coin in coins_list:
                        if cg_coin['symbol'] == coin.name.lower():
                            coin_id = cg_coin['id']
                            print(coin_id)
                            try:
                                time.sleep(2)
                                coin_price = cg.get_price(ids=coin_id,
                                                          vs_currencies='usd')
                                print(coin_price)
                            except Exception as e:
                                print(e)
                            else:
                                if coin_price[coin_id]:
                                    coin.cost_in_busd = Decimal(coin_price[coin_id]['usd']) * busd.cost_in_busd
                                    coin.save()
                                    coins.exclude(pk=coin.pk)
                                    print(coin.cost_in_busd)
    except Exception as e:
        print(e)

    if coins:
        if not busd.cost_in_busd:
            result_dict = dft.pcsTokenInfo(busd.name.lower())
            print(result_dict)
            busd.cost_in_busd = Decimal(result_dict['price'])
            busd.save()
            print(busd.cost_in_busd)
        for coin in coins:
            # {'name': 'PancakeSwap Token', 'symbol': 'Cake', 'price': '4.24055384017923644065998435584', 'price_BNB': '0.01455523752570393902803485311494'}
            try:
                print(coin.name)
                result_dict = dft.pcsTokenInfo(coin.name.lower())
                print(result_dict)
                if result_dict:
                    coin.cost_in_busd = Decimal(result_dict['price']) * busd.cost_in_busd
                    time.sleep(2)
                    coin.save()
                    print(coin.cost_in_busd)
            except Exception as e:
                print('exception', e)

    # coins = Coin.objects.all().exclude(name='BUSD')

    # for coin in coins:
    #     flag = False
    #     for i in range(1, 1000):
    #         if flag:
    #             break

    #         url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    #         parameters = {
    #             'start': i ,
    #             'limit': '5000',
    #             'convert': 'USD',
    #         }

    #         headers = {
    #         'Accepts': 'application/json',
    #         'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    #         }

    #         session = Session()
    #         session.headers.update(headers)

    #         try:
    #             response = session.get(url, params=parameters)
    #             data = json.loads(response.text)
    #             pprint(data)
    #             for key, val in data.items():

    #                 if key == 'status' and val['error']:
    #                     print(val['error'])
    #                     flag = True

    #                 if key == 'data':
    #                     for item in val:
    #                         if item['symbol'] == coin.name:
    #                             print(i)
    #                             print(item['symbol'])
    #                             print(item['quote']['USD']['price'])
    #                             flag = True

    #         except (ConnectionError, Timeout, TooManyRedirects) as e:
    #             print(e)
    #             flag = True
