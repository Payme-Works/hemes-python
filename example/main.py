from dotenv import load_dotenv
load_dotenv()

import os
import json
import time

from datetime import datetime

from hermes.stable_api import StableHermes as Hermes

hermes = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))
hermes.connect()

balances = hermes.get_balances()
real_balance = next((item for item in balances if item['type'] == 1), None)

print(f'Real balance: {real_balance["amount"]}\n')

hermes.change_balance('practice')

active = 'EURUSD'

# hermes.start_candles_stream(active, 60, 20)

# while True:
#     candles = hermes.get_realtime_candles(active, 60)

#     candles_timestamps = list(candles.keys())
#     last_candle_timestamps = candles_timestamps[len(candles_timestamps) - 1]

#     last_candle = candles[last_candle_timestamps]

#     print(last_candle)

#     time.sleep(1)

# hermes.stop_candles_stream(active, 60)

# _, order_id = hermes.buy({
#     'type': 'digital',
#     'active': active,
#     'price_amount': 2,
#     'action': 'put',
#     'expiration': 1
# })
# print(f'Order ID: {order_id}')

# result = hermes.wait_for_result(order_id, 120)

# print(f'Time: {datetime.now().strftime("%H:%M:%S")}')
# print(f'Result: {result}')

trend = hermes.get_trend(active, '5M')
print(f'\n[{active}] Trend: {trend}')
