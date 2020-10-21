from hermes.ws.channels.base import Base


class GetInstruments(Base):
    """Class for IQ Option buy websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self, types):

        data = {
            "name": "get-instruments",
            "version": "4.0",
            "body": {"type": types}
        }

        self.send_websocket_request(self.name, data)
