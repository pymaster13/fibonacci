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


class Command(BaseCommand):
    help = 'Test API'

    def handle(self, *args, **options):
    # def retreive_coins_cost():

        coins = Coin.objects.all().exclude(name='BUSD')

        for coin in coins:
            flag = False

            for i in range(1, 1000):
                time.sleep(1)
                print(coin.name)
                print(i)
                if flag:
                    break

                url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
                parameters = {
                    'start': i ,
                    'limit': '5000',
                    'convert': 'USD',
                }

                headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
                }

                session = Session()
                session.headers.update(headers)

                try:
                    response = session.get(url, params=parameters)
                    data = json.loads(response.text)
                    # pprint(data)

                    if data.get('status'):
                        if data['status'].get('error_code'):
                            pprint(data)
                            print(data['status'].get('error_code'))
                            flag = True
                            break

                    for key, val in data.items():
                        if key == 'data':
                            for item in val:
                                if item['symbol'] == coin.name:
                                    print(item['symbol'])
                                    print(item['quote']['USD']['price'])
                                    coin.cost_in_busd = item['quote']['USD']['price']
                                    coin.save()
                                    flag = True
                                    break

                except (ConnectionError, Timeout, TooManyRedirects, JSONDecodeError) as e:
                    print(e)
                    flag = True
                    break
