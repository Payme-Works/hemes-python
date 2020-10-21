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

buy_result, order_id = account.buy(1, 'EURUSD', 'call', 1)
print(buy_result, order_id)

# profile = account.get_profile_async()
# print('\n', profile)

# result = account.get_option_info_v2(10)['msg']
# print('\n', result['closed_options'][2])

closed_order = account.wait_for_order_close(order_id)
print(closed_order)
