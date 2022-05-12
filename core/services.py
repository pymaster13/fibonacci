from core.models import Coin, Address, AdminWallet


def get_main_wallet():

    coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
    admin_address = Address.objects.get(owner_admin=True, coin=coin)
    admin_wallet = AdminWallet.objects.get(wallet_address=admin_address)
    return admin_wallet
