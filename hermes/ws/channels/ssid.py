"""Module for IQ Option API ssid websocket channel."""

from hermes.ws.channels.base import Base


class Ssid(Base):
    """Class for IQ Option API ssid websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "ssid"

    def __call__(self, ssid):
        """Method to send message to ssid websocket channel.

        :param ssid: The session identifier.
        """

        self.send_websocket_request(self.name, ssid)
