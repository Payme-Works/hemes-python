"""Module for IQ Option user websocket channel."""

from hermes.ws.channels.base import Base
import hermes.constants as OP_code


class Get_user_profile_client(Base):
    name = "sendMessage"

    def __call__(self, user_id):

        data = {
            "name": "get-user-profile-client",
            "body": {
                    "user_id": int(user_id)
            },
            "version": "1.0"
        }

        self.send_websocket_request(self.name, data)


class Request_leaderboard_userinfo_deals_client(Base):
    """Class for IQ Option candles websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self, user_id, country_id):

        data = {"name": "request-leaderboard-userinfo-deals-client",
                "body": {"country_ids": [country_id],
                         "requested_user_id": int(user_id)
                         },
                "version": "1.0"
                }

        self.send_websocket_request(self.name, data)


class Get_users_availability(Base):
    """Class for IQ Option candles websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self, user_id):

        data = {
            "name": "get-users-availability",
            "body": {
                    "user_ids": [user_id]
            },
            "version": "1.0"
        }

        self.send_websocket_request(self.name, data)
