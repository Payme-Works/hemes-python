"""Module for IQ Option user websocket channel."""

from hermes.ws.channels.base import Base
import hermes.constants as OP_code


class GetUserProfileClient(Base):
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


class RequestLeaderboardUserinfoDealsClient(Base):
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


class GetUsersAvailability(Base):
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
