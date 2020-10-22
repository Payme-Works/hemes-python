import unittest
import os
import logging
import time
from hermes.stable_api import StableHermes as Hermes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

email = os.getenv("email")
password = os.getenv("password")


class TestCandle(unittest.TestCase):

    def test_candle(self):
        # login
        i_want_money = Hermes(email, password)
        i_want_money.connect()

        i_want_money.change_balance("PRACTICE")
        i_want_money.reset_practice_balance()

        self.assertEqual(i_want_money.check_connect(), True)

        # start test binary option
        all_asset = i_want_money.get_all_open_actives()

        if all_asset["turbo"]["EURUSD"]["open"]:
            actives = "EURUSD"
        else:
            actives = "EURUSD-OTC"

        i_want_money.get_candles(actives, 60, 1000, time.time())

        # realtime candle
        size = "all"

        i_want_money.start_candles_stream(actives, size, 10)
        i_want_money.get_realtime_candles(actives, size)
        i_want_money.stop_candles_stream(actives, size)
