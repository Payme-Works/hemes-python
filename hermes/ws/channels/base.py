"""Module for base IQ Option base websocket channel."""
import time


class Base(object):
    """Class for base IQ Option websocket channel."""
    # pylint: disable=too-few-public-methods

    def __init__(self, api):
        """
        :param api: The instance of :class:`Hermes <hesmes.api.Hermes>`.
        """

        self.api = api

    def send_websocket_request(self, name, msg, request_id=""):
        """Send request to IQ Option server websocket.

        :param str name: The websocket channel name.
        :param dict msg: The websocket channel msg.

        :returns: The instance of :class:`requests.Response`.
        """

        if request_id == '':
            request_id = int(str(time.time()).split('.')[1])
        return self.api.send_websocket_request(name, msg, request_id)
