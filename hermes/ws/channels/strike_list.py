import datetime
from hermes.ws.channels.base import Base


class Strike_list(Base):
    name = "sendMessage"

    def __call__(self, name, duration):
        exp = self.get_digital_expiration_time(duration)

        data = {
            "name": "get-strike-list",
            "body": {"type": "digital-option",
                     "underlying": name,
                     "expiration": int(exp)*1000,
                     "period": duration*60
                     },
            "version": "4.0"
        }

        self.send_websocket_request(self.name, data)

    def get_digital_expiration_time(self, duration):
        exp = int(self.api.timesync.server_timestamp)
        value = datetime.datetime.fromtimestamp(exp)
        minute = int(value.strftime('%M'))
        second = int(value.strftime('%S'))
        ans = exp-exp % 60  # delete second
        ans = ans+(duration-minute % duration)*60

        if exp > ans-10:
            ans = ans+(duration)*60

        return ans
