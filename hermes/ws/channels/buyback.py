"""Module for IQ Option buyback websocket channel."""

from hermes.ws.channels.base import Base


class Buyback(Base):
    """Class for IQ Option subscribe to buyback websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "buyback"

    def __call__(self):
        """Method to send message to buyback websocket channel."""

        pass
