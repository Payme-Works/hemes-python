from dotenv import load_dotenv
load_dotenv()

import os
from hermes.stable_api import StableHermes as Hermes

account = Hermes(os.getenv('EMAIL'), os.getenv('PASSWORD'))

account.change_balance('PRACTICE')

buy = account.buy(2, 'EURUSD', 'call', 1)

profile = account.get_profile_async()
print(profile)
