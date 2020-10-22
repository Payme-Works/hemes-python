from dotenv import load_dotenv
load_dotenv()

import os
import json
import time

from hermes.stable_api import StableHermes as Hermes

hermes = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))
hermes.connect()

balances = hermes.get_balances()
real_balance = next((item for item in balances if item['type'] == 1), None)

print(f'Real balance: {real_balance["amount"]}')

hermes.change_balance('PRACTICE')

_, order_id = hermes.buy({
    'price_amount': 2,
    'active': 'EURUSD',
    'action': 'put',
    'expiration': 1
})
print(order_id)

profit = hermes.get_all_open_actives()
print(json.dumps(profit))
