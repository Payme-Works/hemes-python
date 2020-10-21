from hermes.ws.channels.base import Base


class ClosePosition(Base):
    name = "sendMessage"

    def __call__(self, position_id):
        data = {
            "name": "close-position",
            "version": "1.0",
            "body": {
                "position_id": position_id
            }
        }

        self.send_websocket_request(self.name, data)
