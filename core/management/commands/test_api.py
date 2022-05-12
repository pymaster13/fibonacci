from django.core.management.base import BaseCommand
from web3 import Web3
import time, json
import requests

class Command(BaseCommand):
    help = 'Test API'

    def handle(self, *args, **options):

        bsc = 'https://bsc-dataseed.binance.org/'
        web3 = Web3(Web3.HTTPProvider(bsc))

        print('connected', web3.isConnected())

        address = '0xDC497fBAbe657add9fd5Bd3FacBC64445c5A0fBC'
        balance = web3.eth.get_balance(address)
        print('my balance', balance)

        url_eth = 'https://api.bscscan.com/api'
        TokenAddress = '0x844fa82f1e54824655470970f7004dd90546bb28'
        contract_address = web3.toChecksumAddress(TokenAddress)
        print(contract_address)
        API_ENDPOINT = f'{url_eth}?module=contract&action=getabi&address={str(contract_address)}'
        r = requests.get(url = API_ENDPOINT)
        response = r.json()
        abi = json.loads(response['result'])

        contract = web3.eth.contract(address=contract_address, abi=abi)
        print(contract.functions.storedValue().call())
        totalSupply = contract.functions.totalSupply().call()
        print(totalSupply)
        print(contract.functions.name().call())
        print(contract.functions.symbol().call())
        address = web3.toChecksumAddress(address)
        balance = contract.functions.balanceOf(address).call()
        print(web3.fromWei(balance, 'ether'))

