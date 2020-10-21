from hermes.ws.channels.base import Base


class TradersMoodSubscribe(Base):
    name = "subscribeMessage"

    def __call__(self, active, instrument="turbo-option"):
        data = {
            "name": "traders-mood-changed",
            "params": {
                "routingFilters": {
                    "instrument": instrument,
                    "asset_id": active
                }
            }
        }

        self.send_websocket_request(self.name, data)


class TradersMoodUnsubscribe(Base):
    name = "unsubscribeMessage"

    def __call__(self, active, instrument="turbo-option"):
        data = {
            "name": "traders-mood-changed",
            "params": {
                "routingFilters": {
                    "instrument": instrument,
                    "asset_id": active
                }
            }

        }

        self.send_websocket_request(self.name, data)
