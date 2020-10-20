"""Module for IQ Option candles websocket channel."""

from hermes.ws.channels.base import Base


class GetCandles(Base):
    """Class for IQ Option candles websocket channel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self, active_id, interval, count, endtime):
        """Method to send message to candles websocket channel.

        :param active_id: The active/asset identifier.
        :param duration: The candle duration (timeframe for the candles).
        :param amount: The number of candles you want to have
        """

        data = {
            "name": "get-candles",
            "version": "2.0",
            "body": {
                    "active_id": int(active_id),
                    "size": interval,  # time size sample:if interval set 1 mean get time 0~1 candle
                # int(self.api.timesync.server_timestamp),
                "to": int(endtime),
                "count": count,  # get how many candle
                "": active_id
            }
        }

        self.send_websocket_request(self.name, data)
