from hermes.ws.channels.base import Base


class GetOptions(Base):
    name = "api_game_getoptions"

    def __call__(self, limit, api):
        self.api = api

        data = {
            "limit": int(limit),
            "user_balance_id": int(self.api.balance_id)
        }

        self.send_websocket_request(self.name, data)


class GetOptionsV2(Base):
    name = "sendMessage"

    def __call__(self, limit, instrument_type):
        data = {
            "name": "get-options",
            "body": {
                "limit": limit,
                "instrument_type": instrument_type,
                "user_balance_id": int(self.api.balance_id)
            }
        }

        self.send_websocket_request(self.name, data)
