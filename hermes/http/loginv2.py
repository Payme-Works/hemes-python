"""Module for IQ Option http loginv2 resource."""

from hermes.http.login import Login


class Loginv2(Login):
    """Class for IQ Option loginv2 resource."""
    # pylint: disable=too-few-public-methods

    url = "/".join((Login.url, "v2"))

    def __init__(self, api):
        super(Loginv2, self).__init__(api)
