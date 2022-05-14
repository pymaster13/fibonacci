from django.core.management.base import BaseCommand
from web3 import Web3
import time, json
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from json.decoder import JSONDecodeError

from pprint import pprint

from core.models import Coin, Address, AdminWallet, MetamaskWallet, Transaction
from ido.models import IDO, IDOParticipant

from config.settings import COINMARKETCAP_API_KEY

from pycoingecko import CoinGeckoAPI
# from pythonpancakes import PancakeSwapAPI
import defi.defi_tools as dft
from decimal import getcontext, Decimal

class Command(BaseCommand):
    help = 'Test API'

    def handle(self, *args, **options):
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
                        coin.save()
                        print(coin.cost_in_busd)
                except Exception as e:
                    print('exception', e)


        # for coin in coins:
        #     flag = False

        #     for i in range(1, 1000):
        #         time.sleep(1)
        #         print(coin.name)
        #         print(i)
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
        #             # pprint(data)

        #             if data.get('status'):
        #                 if data['status'].get('error_code'):
        #                     pprint(data)
        #                     print(data['status'].get('error_code'))
        #                     flag = True
        #                     break

        #             for key, val in data.items():
        #                 if key == 'data':
        #                     for item in val:
        #                         if item['symbol'] == coin.name:
        #                             print(item['symbol'])
        #                             print(item['quote']['USD']['price'])
        #                             coin.cost_in_busd = item['quote']['USD']['price']
        #                             coin.save()
        #                             flag = True
        #                             break

        #         except (ConnectionError, Timeout, TooManyRedirects, JSONDecodeError) as e:
        #             print(e)
        #             flag = True
        #             break
