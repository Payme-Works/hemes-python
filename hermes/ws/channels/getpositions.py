from hermes.ws.channels.base import Base
import hermes.global_value as global_value


class GetPositions(Base):
    name = "sendMessage"

    def __call__(self, instrument_type):
        if instrument_type == "digital-option":
            name = "digital-options.get-positions"
        elif instrument_type == "fx-option":
            name = "trading-fx-option.get-positions"
        else:
            name = "get-positions"

        data = {
            "name": name,
            "body": {
                "instrument_type": instrument_type,
                "user_balance_id": int(global_value.balance_id)
            }
        }

        self.send_websocket_request(self.name, data)


class GetPosition(Base):
    name = "sendMessage"

    def __call__(self, position_id):
        data = {
            "name": "get-position",
            "body": {
                "position_id": position_id,
            }
        }

        self.send_websocket_request(self.name, data)


class GetPositionHistory(Base):
    name = "sendMessage"

    def __call__(self, instrument_type):
        data = {
            "name": "get-position-history",
            "body": {
                "instrument_type": instrument_type,
                "user_balance_id": int(global_value.balance_id)
            }
        }

        self.send_websocket_request(self.name, data)


class GetPositionHistoryV2(Base):
    name = "sendMessage"

    def __call__(self, instrument_types, limit, offset, start=0, end=0):
        data = {
            "name": "portfolio.get-history-positions",
            "body": {
                "instrument_types": [instrument_types],
                "limit": limit,
                "offset": offset,
                "start": start,
                "end": end,
                "user_balance_id": int(global_value.balance_id)
            }
        }

        self.send_websocket_request(self.name, data)


class GetDigitalPosition(Base):
    name = "sendMessage"

    def __call__(self, position_id):
        data = {
            "name": "digital-options.get-position",
            "body": {
                "position_id": position_id,
            }
        }

        self.send_websocket_request(self.name, data)
