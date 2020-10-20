"""Module for IQ Option buyV2 websocket channel."""
from hermes.ws.channels.base import Base


class Changebalance(Base):
    """Class for IQ Option buy websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "api_profile_changebalance"

    def __call__(self, balance_id):
        """Method to send message to buyv2 websocket channel.

        :param price: The buying price.
        :param active: The buying active.
        :param option: The buying option.
        :param direction: The buying direction.
        """

        data = {
            "balance_id": balance_id
        }

        self.send_websocket_request(self.name, data)
