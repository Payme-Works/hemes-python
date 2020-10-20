"""Module for IQ Option setactives websocket channel."""

from hermes.ws.channels.base import Base


class SetActives(Base):
    """Class for IQ Option setactives websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "setActives"

    def __call__(self, actives):
        """Method to send message to setactives websocket channel.

        :param actives: The list of actives identifiers.
        """

        data = {"actives": actives}

        self.send_websocket_request(self.name, data)
