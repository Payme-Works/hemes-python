"""Module for IQ Option http login resource."""

from hermes.http.resource import Resource


class Logout(Resource):
    """Class for IQ Option login resource."""
    # pylint: disable=too-few-public-methods

    url = ""

    def _post(self, data=None, headers=None):
        """Send get request for IQ Option API login http resource.

        :returns: The instance of :class:`requests.Response`.
        """

        return self.api.send_http_request_v2(method="POST", url="https://auth.iqoption.com/api/v1.0/logout", data=data, headers=headers)

    def __call__(self):

        return self._post()
