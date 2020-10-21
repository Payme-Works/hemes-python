from hermes.ws.channels.base import Base
import hermes.global_value as global_value


class BuyPlaceOrderTemp(Base):
    name = "sendMessage"

    def __call__(self,
                 instrument_type, instrument_id,
                 side, amount, leverage,
                 type, limit_price, stop_price,

                 stop_lose_kind, stop_lose_value,
                 take_profit_kind, take_profit_value,

                 use_trail_stop, auto_margin_call,
                 use_token_for_commission):
        data = {
            "name": "place-order-temp",
            "version": "4.0",
            "body": {
                "instrument_type": str(instrument_type),
                "instrument_id": str(instrument_id),
                "side": str(side),  # "buy"/"sell"
                "amount": float(amount),  # money you want buy/sell
                "leverage": int(leverage),

                "type": type,  # "market"/"limit"/"stop"
                # for type="limit"/"stop"
                # only working by set type="limit"
                "limit_price": (limit_price),
                "stop_price": (stop_price),  # only working by set type="stop"

                # /************set stop loose/take *******************/
                "stop_lose_kind": (stop_lose_kind),
                "stop_lose_value": (stop_lose_value),

                "take_profit_kind": (take_profit_kind),
                "take_profit_value": (take_profit_value),

                "use_trail_stop": bool(use_trail_stop),  # Trailing Stop
                # this is "Use Balance to Keep Position Open",if you want take_profit_value and stop_lose_value all be "Not Set",auto_margin_call need to True
                "auto_margin_call": bool(auto_margin_call),


                "use_token_for_commission": bool(use_token_for_commission),
                "user_balance_id": int(global_value.balance_id),
                "client_platform_id": "9",  # important can not delete,9 mean your platform is linux
            }
        }

        self.send_websocket_request(self.name, data)
