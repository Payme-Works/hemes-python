import datetime
import time
from hermes.ws.channels.base import Base
import logging
import hermes.global_value as global_value
from hermes.expiration import get_expiration_time


class Buyv3(Base):

    name = "sendMessage"

    def __call__(self, price, active, direction, duration, request_id):
        exp, idx = get_expiration_time(
            int(self.api.timesync.server_timestamp), duration)

        if idx < 5:
            option = 3  # "turbo"
        else:
            option = 1  # "binary"

        data = {
            "body": {
                "price": price,
                "active_id": active,
                "expired": int(exp),
                "direction": direction.lower(),
                "option_type_id": option,
                "user_balance_id": int(global_value.balance_id)
            },
            "name": "binary-options.open-option",
            "version": "1.0"
        }

        self.send_websocket_request(self.name, data, str(request_id))


class Buyv3_by_raw_expired(Base):
    name = "sendMessage"

    def __call__(self, price, active, direction, option, expired, request_id):
        if option == "turbo":
            option_id = 3  # "turbo"
        elif option == "binary":
            option_id = 1  # "binary"

        data = {
            "body": {"price": price,
                     "active_id": active,
                     "expired": int(expired),
                     "direction": direction.lower(),
                     "option_type_id": option_id,
                     "user_balance_id": int(global_value.balance_id)
                     },
            "name": "binary-options.open-option",
            "version": "1.0"
        }

        self.send_websocket_request(self.name, data, str(request_id))
