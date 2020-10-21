from dotenv import load_dotenv
load_dotenv()

import os
from hermes.stable_api import StableHermes as Hermes

account = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))
account.connect()

balances = account.get_balances()
real_balance = next((item for item in balances if item['type'] == 1), None)

print('Real balance: {}'.format(real_balance['amount']))

account.change_balance('PRACTICE')

_, order_id = account.buy({
    'price_amount': 2,
    'active': 'EURUSD',
    'action': 'put',
    'expiration': 1
})
print(order_id)

profile = account.get_profile_async()
print('\n', profile)
