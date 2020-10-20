"""Module for IQ Option buyV2 websocket channel."""
import hermes.global_value as global_value
from hermes.ws.channels.base import Base
from hermes.expiration import get_expiration_time


class Buyv2(Base):
    """Class for IQ Option buy websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self, price, active, direction, duration):
        """Method to send message to buyv2 websocket channel.
        :param price: The buying price.
        :param active: The buying active.
        :param direction: The buying direction.
        """

        exp, idx = get_expiration_time(
            int(self.api.timesync.server_timestamp), duration)

        if idx < 5:
            option = 3  # turbo
        else:
            option = 1  # non-turbo / binary

        data = {
            "price": price,
            "act": active,
            "exp": int(exp),
            "type": option,
            "direction": direction.lower(),
            "user_balance_id": int(global_value.balance_id),
            "time": self.api.timesync.server_timestamp
        }

        self.send_websocket_request(self.name, data)
