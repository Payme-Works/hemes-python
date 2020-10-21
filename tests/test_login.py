import unittest
import os
from hermes.stable_api import StableHermes as Hermes

email = os.getenv("email")
password = os.getenv("password")


class TestLogin(unittest.TestCase):

    def test_login(self):
        i_want_money = Hermes(email, password)
        i_want_money.connect()

        i_want_money.change_balance("PRACTICE")
        # i_want_money.reset_practice_balance()

        self.assertEqual(i_want_money.check_connect(), True)

        balances = i_want_money.get_balances()
        print(balances)
