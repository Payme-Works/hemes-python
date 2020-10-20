from hermes.ws.channels.base import Base


class Get_order(Base):
    name = "sendMessage"

    def __call__(self, order_id):
        data = {
            "name": "get-order",
            "body": {
                "order_id": int(order_id)
            }
        }

        self.send_websocket_request(self.name, data)
