from dotenv import load_dotenv
load_dotenv()

import os
import json

from hermes.stable_api import StableHermes as Hermes

hermes = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))
hermes.connect()

balances = hermes.get_balances()
real_balance = next((item for item in balances if item['type'] == 1), None)

print(f'Real balance: {real_balance["amount"]}\n')

hermes.change_balance('practice')

_, order_id = hermes.buy({
    'type': 'digital',
    'active': 'EURUSD',
    'price_amount': 2,
    'action': 'put',
    'expiration': 1
})
print(order_id)

# all_open_actives = hermes.get_all_open_actives()
# print(json.dumps(all_open_actives))

active = 'EURUSD'

order = hermes.wait_for_result(order_id, 120)
print(order)

trend = hermes.get_trend(active, '5M')
print(f'\n[{active}] Trend: {trend}')
