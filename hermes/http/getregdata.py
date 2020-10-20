"""Module for IQ Option http getregdata resource."""

from hermes.http.resource import Resource
from hermes.http.register import Register


class Getprofile(Resource):
    """Class for IQ Option getregdata resource."""
    # pylint: disable=too-few-public-methods

    url = "/".join((Register.url, "getregdata"))

    def _get(self):
        """Send get request for IQ Option API getregdata http resource.

        :returns: The instance of :class:`requests.Response`.
        """

        return self.send_http_request("GET")

    def __call__(self):
        """Method to get IQ Option API getregdata http request.

        :returns: The instance of :class:`requests.Response`.
        """

        return self._get()
