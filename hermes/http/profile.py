"""Module for IQ Option profile resource."""

from hermes.http.resource import Resource


class Profile(Resource):
    """Class for IQ Option profile resource."""
    # pylint: disable=too-few-public-methods

    url = "profile"
