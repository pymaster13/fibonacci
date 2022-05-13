from decimal import Decimal, getcontext
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

from core.models import Coin, Address, AdminWallet, MetamaskWallet, Transaction
from ido.models import IDO, IDOParticipant

from config.settings import COINMARKETCAP_API_KEY


def get_main_wallet():
    coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
    admin_address = Address.objects.get(owner_admin=True, coin=coin)
    admin_wallet = AdminWallet.objects.get(wallet_address=admin_address)
    return admin_wallet


def get_custom_admin_wallets():
    coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
    admin_addresses = Address.objects.filter(owner_admin=True)
    admin_wallets = []
    if admin_addresses:
        for address in admin_addresses:
            if address.coin != coin:
                admin_wallets.append(AdminWallet.objects.get(wallet_address=address))

    return admin_wallets


def get_smartcontract_by_coin(coin):
    smart = Address.objects.get(owner_admin=False, coin=coin)
    return smart


def divide(number, precision):
    getcontext().prec = precision
    result = str(number)
    while len(result) < precision + 1:
        result = '0' + result
    new_result = result[:len(result)-precision] + '.' + result[len(result)-precision:]
    dec = Decimal(new_result)

    return dec


def distribute_tokens(wallet: AdminWallet, smartcontract: Address, amount: Decimal):
    ido = IDO.objects.get(coin=smartcontract.coin)
    if not ido.charge_manually:
        getcontext().prec = wallet.decimal
        participants = IDOParticipant.objects.filter(ido=ido)
        print('all_participants', participants)
        common_alloc = Decimal(sum([part.allocation for part in participants if part.allocation]))
        print(common_alloc)
        for participant in participants:
            print(participant)
            if participant.allocation:
                part = Decimal(participant.allocation) / common_alloc
                print(f'{part=}')
                metamask = MetamaskWallet.objects.get(user=participant.user)
                print(f'{wallet=}')
                tokens = part * amount
                print(repr(tokens))
                Transaction.objects.create(
                                    address_from=smartcontract,
                                    address_to=metamask.wallet_address,
                                    coin=smartcontract.coin,
                                    amount=tokens
                                    )


def fill_admin_custom_wallet(wallet: AdminWallet, smartcontract: Address, amount: Decimal) -> Transaction:
    transaction = Transaction.objects.create(
                                address_from=smartcontract,
                                address_to=wallet.wallet_address,
                                coin=smartcontract.coin,
                                amount=amount)
    return transaction


def get_current_token_price():
    for i in range(1, 100):
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
            for key, val in data.items():
                if key == 'data':
                    for item in val:
                        if item['symbol'] == 'BOR':
                            print(i)
                            print(item['symbol'])
                            print(item['quote']['USD']['price'])
                            break
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
            break