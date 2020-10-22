from dotenv import load_dotenv
load_dotenv()

import os
import json

from hermes.stable_api import StableHermes as Hermes

hermes = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))
hermes.connect()

balances = hermes.get_balances()
real_balance = next((item for item in balances if item['type'] == 1), None)

print('Real balance: {}'.format(real_balance['amount']))

hermes.change_balance('PRACTICE')

# _, order_id = hermes.buy({
#     'price_amount': 2,
#     'active': 'EURUSD',
#     'action': 'put',
#     'expiration': 1
# })
order_id = 7532320614
print(order_id)

# profile = account.get_profile_async()
# print('\n', profile)

orders = hermes.get_history(2)
print(json.dumps(orders))

# hermes.wait_for_order_close(7532320614)
