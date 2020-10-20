"""Module for IQ Option billing resource."""

from hermes.http.resource import Resource


class Billing(Resource):
    """Class for IQ Option billing resource."""
    # pylint: disable=too-few-public-methods

    url = "billing"
