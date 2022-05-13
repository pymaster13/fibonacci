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

from core.services import (get_custom_admin_wallets, get_smartcontract_by_coin,
                           divide, fill_admin_custom_wallet, distribute_tokens)

from config.settings import COINMARKETCAP_API_KEY

"""
Run dramatiq workers - "dramatiq core.tasks"
"""


@dramatiq.actor
def process():
    """Very simple task for demonstrating purpose."""

    print('Start processsss')

    api_key = 'M7YIPI177FP25ETG47N7G112DXXWNMATS6'

    admin_wallets = get_custom_admin_wallets()

    for wallet in admin_wallets:
        smart = get_smartcontract_by_coin(coin=wallet.wallet_address.coin)
        address = wallet.wallet_address.address

        url = f'https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={smart}&address={address}&tag=latest&apikey={api_key}'
        response = requests.get(url)
        data = response.json()

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

    # contract = '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
    # contract2= '0x57d90b64a1a57749b0f932f1a3395792e12e7055'
    # account = '0x4e83362442b8d1bec281594cea3050c8eb01311c'
    # account2 = '0xe04f27eb70e025b78871a2ad7eabe85e61212761'

    # # url = f'https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract}&address={account}&page=1&offset=100&startblock=0&endblock=27025780&sort=asc&apikey={api_key}'
    # response = requests.get(url)
    # print(response.json())

@dramatiq.actor
def retreive_coins_cost():

    coins = Coin.objects.all().exclude(name='BUSD')

    for coin in coins:
        flag = False
        for i in range(1, 1000):
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
                pprint(data)
                for key, val in data.items():

                    if key == 'status' and val['error']:
                        print(val['error'])
                        flag = True

                    if key == 'data':
                        for item in val:
                            if item['symbol'] == coin.name:
                                print(i)
                                print(item['symbol'])
                                print(item['quote']['USD']['price'])
                                flag = True

            except (ConnectionError, Timeout, TooManyRedirects) as e:
                print(e)
                flag = True
