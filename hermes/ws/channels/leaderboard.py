from hermes.ws.channels.base import Base


class LeaderBoard(Base):
    name = "sendMessage"

    def __call__(self, country_id, user_country_id, from_position, to_position, near_traders_country_count, near_traders_count, top_country_count, top_count, top_type):
        data = {
            "name": "request-leaderboard-deals-client",
            "version": "1.0",
            "body": {
                    "country_id": country_id,
                    "user_country_id": user_country_id,
                "from_position": from_position,
                "to_position": to_position,
                "near_traders_country_count": near_traders_country_count,
                "near_traders_count": near_traders_count,
                "top_country_count": top_country_count,
                "top_count": top_count,
                "top_type": top_type
            }
        }

        self.send_websocket_request(self.name, data)
