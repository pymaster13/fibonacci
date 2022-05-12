from django.core.management.base import BaseCommand
from web3 import Web3
import time, json
import requests

class Command(BaseCommand):
    help = 'Test API'

    def handle(self, *args, **options):

        api_key = 'M7YIPI177FP25ETG47N7G112DXXWNMATS6'

        contract = '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
        contract2= '0x57d90b64a1a57749b0f932f1a3395792e12e7055'
        account = '0x4e83362442b8d1bec281594cea3050c8eb01311c'
        account2 = '0xe04f27eb70e025b78871a2ad7eabe85e61212761'

        # url = f'https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract}&address={account}&page=1&offset=100&startblock=0&endblock=27025780&sort=asc&apikey={api_key}'
        url = f'https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={contract2}&address={account2}&tag=latest&apikey={api_key}'
        response = requests.get(url)
        print(response.json())
