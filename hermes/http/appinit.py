from hermes.http.resource import Resource


class AppInit(Resource):
    """Class for IQ Option login resource."""
    # pylint: disable=too-few-public-methods

    url = "appinit"

    def _get(self, data=None, headers=None):
        """Send get request for IQ Option API appinit http resource.

        :returns: The instance of :class:`requests.Response`.
        """

        return self.send_http_request("GET", data=data, headers=headers)

    def __call__(self):
        """Method to get IQ Option API appinit http request.

        :returns: The instance of :class:`requests.Response`.
        """

        return self._get()
