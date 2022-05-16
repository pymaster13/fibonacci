from decimal import Decimal, getcontext
import json
from numpy import amax
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from django.contrib.auth import get_user_model
from administrator.models import VIPUser

from core.exceptions import AdminWalletIsEmptyError, CommissionError, MetamaskWalletExistsError
from core.models import Coin, Address, AdminWallet, MetamaskWallet, Transaction
from ido.models import IDO, IDOParticipant

from config.settings import COINMARKETCAP_API_KEY


User = get_user_model()


def get_main_wallet():
    coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
    admin_address = Address.objects.get(owner_admin=True, coin=coin)
    admin_wallet = AdminWallet.objects.get(wallet_address=admin_address)
    return admin_wallet


def get_custom_admin_wallets():
    print('start get_custom_admin_wallets')
    coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
    admin_addresses = Address.objects.filter(owner_admin=True).exclude(coin=coin)
    admin_wallets = []
    if admin_addresses:
        for address in admin_addresses:
            admin_wallets.append(AdminWallet.objects.get(wallet_address=address))
    print('admin_wallets')
    print(admin_wallets)
    return admin_wallets


def divide(number, precision):
    getcontext().prec = precision
    result = str(number)
    while len(result) < precision + 1:
        result = '0' + result
    new_result = result[:len(result)-precision] + '.' + result[len(result)-precision:]
    dec = Decimal(new_result)

    return dec


def referal_by_income(user: User, admin_wallet: AdminWallet, smartcontract: Address, tokens: Decimal) -> Decimal:
    print('referal_by_income')
    print(f'{user=}')
    ido = IDO.objects.get(smartcontract=smartcontract)
    ido_participant = IDOParticipant.objects.get(ido=ido, user=user)

    if ido_participant.refund_allocation < 650:
        print('REFUND < 650')
        return tokens

    getcontext().prec = admin_wallet.decimal

    try:
        metamask = MetamaskWallet.objects.get(user=user)
    except Exception:
        raise MetamaskWalletExistsError('Такой кошелек не привязан ни к какому аккаунту.')

    coin = admin_wallet.wallet_address.coin
    commission = Decimal(0.35)

    inviters = user.inviters
    if not user.inviters:
        print('нет инвайтеров')
        Transaction.objects.create(
                        address_from=metamask.wallet_address,
                        address_to=admin_wallet.wallet_address,
                        coin=coin,
                        amount=commission*tokens,
                        commission=True
                        )
        print(tokens, commission)
        print(tokens - commission * tokens)

        ido_participant.income_from_income += float(commission * tokens * coin.cost_in_busd)
        ido_participant.save()
        print('income', ido_participant.income_from_income)

        return tokens - commission*tokens

    vip_users_objects = VIPUser.objects.all()
    vip_users = []
    for vip_us in vip_users_objects:
        if vip_us.user in inviters:
            vip_users.append(vip_us.user)

    print(f'старт {vip_users=}')

    users_percents = []

    flag = False
    for index, inviter_user in enumerate(inviters):
        if flag:
            break

        if index == 0:
            if inviter_user not in vip_users:
                print(index, inviter_user, Decimal(0.06))
                users_percents.append((inviter_user, Decimal(0.06)))
            else:
                vip = vip_users_objects.get(user=inviter_user)
                print('vip')
                profit = Decimal(0.01 * vip.referal_profit)
                print(index, vip.user, vip.referal_profit, profit)
                users_percents.append((inviter_user, profit))
                vip_users.remove(inviter_user)

        if index == 1:
            if inviter_user not in vip_users:
                print(index, inviter_user, Decimal(0.04))
                users_percents.append((inviter_user, Decimal(0.04)))
            else:
                vip = vip_users_objects.get(user=inviter_user)
                print('vip')
                profit = Decimal(0.01 * vip.referal_profit)
                print(index, vip.user, vip.referal_profit, profit)
                users_percents.append((inviter_user, profit))
                vip_users.remove(inviter_user)

        if index == 2:
            if inviter_user not in vip_users:
                print(index, inviter_user, Decimal(0.02))
                users_percents.append((inviter_user, Decimal(0.02)))
            else:
                vip = vip_users_objects.get(user=inviter_user)
                print('vip')
                profit = Decimal(0.01 * vip.referal_profit)
                print(index, vip.user, vip.referal_profit, profit)
                users_percents.append((inviter_user, profit))
                vip_users.remove(inviter_user)

        if index == 3:
            for inviter_user in vip_users:
                print('vip')
                vip = vip_users_objects.get(user=inviter_user)
                profit = Decimal(0.01 * vip.referal_profit)
                print(index, vip.user, vip.referal_profit, profit)
                users_percents.append((inviter_user, profit))
                vip_users.remove(inviter_user)
            flag = True

    print(f'конец, {vip_users=}')
    print(users_percents)

    summ_commission = sum(c for _, c in users_percents)
    if summ_commission > Decimal(0.35):
        raise CommissionError('Бонусы инвайтерам с дохода пользователя больше 35%.')

    print(f'{summ_commission=}')

    for u, percent in users_percents:
        try:
            print('metamask', u.email)
            metamask_inviter = MetamaskWallet.objects.get(user=u)
        except Exception:
            raise MetamaskWalletExistsError('Такой кошелек не привязан ни к какому аккаунту.')

        trans = Transaction.objects.create(
                    address_from=metamask.wallet_address,
                    address_to=metamask_inviter.wallet_address,
                    coin=coin,
                    amount=tokens*percent,
                    referal=True
                )
        print('trans for inviter')
        print(u.email)
        print(f'{trans.amount}')

    print(12)

    trans = Transaction.objects.create(
                    address_from=metamask.wallet_address,
                    address_to=admin_wallet.wallet_address,
                    coin=coin,
                    amount=tokens*(commission-summ_commission),
                    commission=True
                    )
    print('trans for admin')
    print(trans.amount)

    print(13)

    print('income from income in tokens', commission * tokens)
    print('coin', coin.name)
    print('cost', coin.cost_in_busd)
    if coin.cost_in_busd:
        ido_participant.income_from_income += float(commission * tokens * coin.cost_in_busd)
        ido_participant.save()
    print('income in busd', ido_participant.income_from_income)

    return tokens - commission*tokens


def distribute_tokens(wallet: AdminWallet, smartcontract: Address, amount: Decimal):
    ido = IDO.objects.get(coin=smartcontract.coin)
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

            tokens = referal_by_income(participant.user, wallet, smartcontract, tokens)

            print(repr(tokens))
            Transaction.objects.create(
                                address_from=smartcontract,
                                address_to=metamask.wallet_address,
                                coin=smartcontract.coin,
                                amount=tokens
                                )

def charge_tokens(wallet: AdminWallet, smartcontract: Address, amount: Decimal):
    if wallet.balance == 0:
        raise AdminWalletIsEmptyError('Кошелек главного аккаунта пуст.')
    ido = IDO.objects.get(coin=smartcontract.coin)
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
                                amount=amount,
                                fill_up=True)
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