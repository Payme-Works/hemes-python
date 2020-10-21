from hermes.ws.channels.base import Base


class GetBalances(Base):
    name = "sendMessage"

    def __call__(self):
        data = {
            "name": "get-balances",
            "version": "1.0"
        }

        self.send_websocket_request(self.name, data)
