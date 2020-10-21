import unittest
import os
import logging
from hermes.stable_api import StableHermes as Hermes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

email = os.getenv("email")
password = os.getenv("password")


class TestBinaryOption(unittest.TestCase):
    def test_binary_option(self):
        i_want_money = Hermes(email, password)
        i_want_money.change_balance("PRACTICE")
        i_want_money.reset_practice_balance()

        self.assertEqual(i_want_money.check_connect(), True)

        all_asset = i_want_money.get_all_open_time()

        if all_asset["turbo"]["EURUSD"]["open"]:
            actives = "EURUSD"
        else:
            actives = "EURUSD-OTC"

        money = 1
        action_call = "call"
        expirations_mode = 1

        check_call, id_call = i_want_money.buy(
            money, actives, action_call, expirations_mode)

        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)

        i_want_money.sell_option(id_call)

        action_call = "put"

        check_put, id_put = i_want_money.buy(
            money, actives, action_call, expirations_mode)

        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)

        i_want_money.sell_option(id_put)
        i_want_money.check_win_v2(id_put)

        i_want_money.get_binary_option_detail()

        i_want_money.get_all_profit()

        is_successful = i_want_money.get_betinfo(id_put)

        self.assertTrue(is_successful)

        i_want_money.get_option_info(10)
