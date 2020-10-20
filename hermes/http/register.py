"""Module for IQ Option register resource."""

from hermes.http.resource import Resource


class Register(Resource):
    """Class for IQ Option register resource."""
    # pylint: disable=too-few-public-methods

    url = "register"
