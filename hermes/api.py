import json
import threading
import requests
import ssl
import atexit
import logging

from collections import deque

from hermes.http.login import Login
from hermes.http.loginv2 import LoginV2
from hermes.http.logout import Logout
from hermes.http.login2fa import Login2FA
from hermes.http.send_sms import SMSSender
from hermes.http.verify import Verify
from hermes.http.getprofile import GetProfile
from hermes.http.auth import Auth
from hermes.http.token import Token
from hermes.http.appinit import AppInit
from hermes.http.billing import Billing
from hermes.http.buyback import Buyback
from hermes.http.changebalance import ChangeBalance
from hermes.http.events import Events
from hermes.ws.client import WebsocketClient
from hermes.ws.channels.getbalances import *
from hermes.ws.channels.ssid import SSID
from hermes.ws.channels.subscribe import *
from hermes.ws.channels.unsubscribe import *
from hermes.ws.channels.setactives import SetActives
from hermes.ws.channels.candles import GetCandles
from hermes.ws.channels.buyv2 import BuyV2
from hermes.ws.channels.buyv3 import *
from hermes.ws.channels.user import *
from hermes.ws.channels.api_game_betinfo import GameBetInfo
from hermes.ws.channels.instruments import GetInstruments
from hermes.ws.channels.get_financial_information import GetFinancialInformation
from hermes.ws.channels.strikelist import StrikeList
from hermes.ws.channels.leaderboard import LeaderBoard
from hermes.ws.channels.traders_mood import TradersMoodSubscribe
from hermes.ws.channels.traders_mood import TradersMoodUnsubscribe
from hermes.ws.channels.technicalindicators import TechnicalIndicators
from hermes.ws.channels.buyplaceordertemp import BuyPlaceOrderTemp
from hermes.ws.channels.getorder import GetOrder
from hermes.ws.channels.get_deferred_orders import GetDeferredOrders
from hermes.ws.channels.getpositions import *
from hermes.ws.channels.getavailableleverages import GetAvailableLeverages
from hermes.ws.channels.cancelorder import CancelOrder
from hermes.ws.channels.closeposition import ClosePosition
from hermes.ws.channels.getovernightfee import GetOvernightFee
from hermes.ws.channels.heartbeat import Heartbeat
from hermes.ws.channels.digital_option import *
from hermes.ws.channels.api_game_getoptions import *
from hermes.ws.channels.selloption import SellOption
from hermes.ws.channels.selldigitaloption import SellDigitalOption
from hermes.ws.channels.changetpsl import ChangeTPSL
from hermes.ws.channels.change_auto_margin_call import ChangeAutoMarginCall
from hermes.ws.objects.timesync import TimeSync
from hermes.ws.objects.profile import Profile
from hermes.ws.objects.candles import Candles
from hermes.ws.objects.listinfodata import ListInfoData
from hermes.ws.objects.betinfo import GameBetInfoData
from collections import defaultdict


def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))


requests.packages.urllib3.disable_warnings()


class Hermes(object):
    socket_option_opened = {}
    socket_option_closed = {}
    time_sync = TimeSync()
    profile = Profile()
    candles = Candles()
    list_info_data = ListInfoData()
    api_option_init_all_result = []
    api_option_init_all_result_v2 = []

    underlying_list_data = None
    position_changed = None
    instrument_quites_generated_data = nested_dict(2, dict)
    instrument_quotes_generated_raw_data = nested_dict(2, dict)
    instrument_quites_generated_timestamp = nested_dict(2, dict)
    strike_list = None
    leaderboard_deals_client = None

    order_async = nested_dict(2, dict)
    opened_options = {}
    closed_options = {}
    order_binary = {}
    game_betinfo = GameBetInfoData()
    instruments = None
    financial_information = None
    buy_id = None
    buy_order_id = None
    traders_mood = {}
    technical_indicators = {}
    order_data = None
    positions = None
    position = None
    deferred_orders = None
    position_history = None
    position_history_v2 = None
    available_leverages = None
    order_canceled = None
    close_position_data = None
    overnight_fee = None

    digital_option_placed_id = {}
    live_deal_data = nested_dict(3, deque)

    subscribe_commission_changed_data = nested_dict(2, dict)
    real_time_candles = nested_dict(3, dict)
    real_time_candles_max_dict_table = nested_dict(2, dict)
    candle_generated_check = nested_dict(2, dict)
    candle_generated_all_size_check = nested_dict(1, dict)

    api_game_get_options_result = None
    sold_options_respond = None
    sold_digital_options_respond = None
    tpsl_changed_respond = None
    auto_margin_call_changed_respond = None
    top_assets_updated_data = {}
    get_options_v2_data = None

    buy_multi_result = None
    buy_multi_option = {}

    result = None
    training_balance_reset_request = None
    balances_raw = None
    user_profile_client = None
    leaderboard_userinfo_deals_client = None
    users_availability = None

    check_websocket_if_connect = None
    ssl_mutual_exclusion = False
    ssl_mutual_exclusion_write = False
    ssid = None
    check_websocket_if_error = False
    websocket_error_reason = None
    balance_id = None

    def __init__(self, host, username, password, proxies=None):
        """
        :param str host: The hostname or ip address of a IQ Option server.
        :param str username: The username of a IQ Option server.
        :param str password: The password of a IQ Option server.
        :param dict proxies: (optional) The http request proxies.
        """
        self.https_url = "https://{host}/api".format(host=host)
        self.wss_url = "wss://{host}/echo/websocket".format(host=host)
        self.websocket_client = None
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False
        self.username = username
        self.password = password
        self.token_login2fa = None
        self.token_sms = None
        self.proxies = proxies
        self.buy_successful = None
        self.websocket_thread = None

    def prepare_http_url(self, resource):
        """Construct http url from resource url.

        :param resource: The instance of
            :class:`Resource <hermes.http.resource.Resource>`.

        :returns: The full url to IQ Option http resource.
        """
        return "/".join((self.https_url, resource.url))

    def send_http_request(self, resource, method, data=None, params=None, headers=None):
        """Send http request to IQ Option server.

        :param resource: The instance of
            :class:`Resource <hermes.http.resource.Resource>`.
        :param str method: The http request method.
        :param dict data: (optional) The http request data.
        :param dict params: (optional) The http request params.
        :param dict headers: (optional) The http request headers.

        :returns: The instance of :class:`Response <requests.Response>`.
        """
        logger = logging.getLogger(__name__)
        url = self.prepare_http_url(resource)

        logger.debug(url)

        response = self.session.request(
            method=method,
            url=url,
            data=data,
            params=params,
            headers=headers,
            proxies=self.proxies
        )
        logger.debug(response)
        logger.debug(response.text)
        logger.debug(response.headers)
        logger.debug(response.cookies)

        response.raise_for_status()
        return response

    def send_http_request_v2(self, url, method, data=None, params=None, headers=None):
        """Send http request to IQ Option server.

        :param url: The requested URL.
        :param str method: The http request method.
        :param dict data: (optional) The http request data.
        :param dict params: (optional) The http request params.
        :param dict headers: (optional) The http request headers.

        :returns: The instance of :class:`Response <requests.Response>`.
        """
        logger = logging.getLogger(__name__)

        logger.debug(
            method+": "+url+" headers: " +
            str(self.session.headers) + " cookies: " +
            str(self.session.cookies.get_dict())
        )

        response = self.session.request(
            method=method,
            url=url,
            data=data,
            params=params,
            headers=headers,
            proxies=self.proxies
        )
        logger.debug(response)
        logger.debug(response.text)
        logger.debug(response.headers)
        logger.debug(response.cookies)

        return response

    @property
    def websocket(self):
        """Property to get websocket.

        :returns: The instance of :class:`WebSocket <websocket.WebSocket>`.
        """
        return self.websocket_client.wss

    def send_websocket_request(self, name, msg, request_id="", no_force_send=True):
        """Send websocket request to IQ Option server."""
        logger = logging.getLogger(__name__)

        data = json.dumps(dict(name=name, msg=msg, request_id=request_id))

        while (self.ssl_mutual_exclusion or self.ssl_mutual_exclusion_write) and no_force_send:
            pass

        self.ssl_mutual_exclusion_write = True

        self.websocket.send(data)

        logger.debug(data)

        self.ssl_mutual_exclusion_write = False

    @property
    def logout(self):
        """Property for get IQ Option http login resource.

        :returns: The instance of :class:`Login <hermes.http.login.Login>`.
        """
        return Logout(self)

    @property
    def login(self):
        """Property for get IQ Option http login resource.

        :returns: The instance of :class:`Login <hermes.http.login.Login>`.
        """
        return Login(self)

    @property
    def login_2fa(self):
        """Property for get IQ Option http login 2FA resource.

        :returns: The instance of :class:`Login2FA <hermes.http.login2fa.Login2FA>`.
        """
        return Login2FA(self)

    @property
    def send_sms_code(self):
        """Property for get IQ Option http send sms code resource.

        :returns: The instance of :class:`SMSSender <hermes.http.send_sms.SMSSender>`.
        """
        return SMSSender(self)

    @property
    def verify_2fa(self):
        """Property for get IQ Option http verify 2FA resource.

        :returns: The instance of :class:`Verify <hermes.http.verify.Verify>`.
        """
        return Verify(self)

    @property
    def loginv2(self):
        """Property for get IQ Option http login v2 resource.

        :returns: The instance of :class:`LoginB2 <hermes.http.loginv2.LoginB2>`.
        """
        return LoginV2(self)

    @property
    def auth(self):
        """Property for get IQ Option http auth resource.

        :returns: The instance of :class:`Auth <hermes.http.auth.Auth>`.
        """
        return Auth(self)

    @property
    def appinit(self):
        """Property for get IQ Option http appinit resource.

        :returns: The instance of :class:`AppInit <hermes.http.appinit.AppInit>`.
        """
        return AppInit(self)

    @property
    def token(self):
        """Property for get IQ Option http token resource.

        :returns: The instance of :class:`Token <hermes.http.auth.Token>`.
        """
        return Token(self)

    def reset_training_balance(self):
        self.send_websocket_request(name="sendMessage", msg={
            "name": "reset-training-balance",
            "version": "2.0"
        }
        )

    @property
    def change_balance(self):
        """Property for get IQ Option http change balance resource.

        :returns: The instance of :class:`ChangeBalance <hermes.http.changebalance.ChangeBalance>`.
        """
        return ChangeBalance(self)

    @property
    def events(self):
        return Events(self)

    @property
    def billing(self):
        """Property for get IQ Option http billing resource.

        :returns: The instance of :class:`Billing <hermes.http.billing.Billing>`.
        """
        return Billing(self)

    @property
    def buyback(self):
        """Property for get IQ Option http buyback resource.

        :returns: The instance of :class:`Buyback <hermes.http.buyback.Buyback>`.
        """
        return Buyback(self)

    @property
    def get_profile(self):
        """Property for get IQ Option http getprofile resource.

        :returns: The instance of :class:`Login <hermes.http.getprofile.GetProfile>`.
        """
        return GetProfile(self)

    @property
    def get_balances(self):
        """Property for get IQ Option http get_profile resource.

        :returns: The instance of :class:`GetProfile <hermes.http.getprofile.GetProfile>`.
        """
        return GetBalances(self)

    @property
    def get_instruments(self):
        return GetInstruments(self)

    @property
    def get_financial_information(self):
        return GetFinancialInformation(self)

    @property
    def subscribe_live_deal(self):
        return SubscribeLiveDeal(self)

    @property
    def unsubscribe_live_deal(self):
        return UnscribeLiveDeal(self)

    @property
    def subscribe_traders_mood(self):
        return TradersMoodSubscribe(self)

    @property
    def unsubscribe_traders_mood(self):
        return TradersMoodUnsubscribe(self)

    @property
    def get_technical_indicators(self):
        return TechnicalIndicators(self)

    @property
    def subscribe(self):
        """Property for get IQ Option websocket subscribe channel.

        :returns: The instance of :class:`Subscribe <hermes.ws.channels.subscribe.Subscribe>`.
        """
        return Subscribe(self)

    @property
    def subscribe_all_size(self):
        return SubscribeCandles(self)

    @property
    def unsubscribe(self):
        """Property for get IQ Option websocket unsubscribe channel.

        :returns: The instance of :class:`Unsubscribe <hermes.ws.channels.unsubscribe.Unsubscribe>`.
        """
        return Unsubscribe(self)

    @property
    def unsubscribe_all_size(self):
        return UnsubscribeCandles(self)

    def portfolio(self, main_name, name, instrument_type, user_balance_id="", limit=1, offset=0, request_id=""):
        request_id = str(request_id)

        msg = None

        if name == "portfolio.order-changed":
            msg = {
                "name": name,
                "version": "1.0",
                "params": {
                    "routingFilters": {"instrument_type": str(instrument_type)}
                }
            }
        elif name == "portfolio.get-positions":
            msg = {
                "name": name,
                "version": "3.0",
                "body": {
                    "instrument_type": str(instrument_type),
                    "limit": int(limit),
                    "offset": int(offset)
                }
            }
        elif name == "portfolio.position-changed":
            msg = {
                "name": name,
                "version": "2.0",
                "params": {
                    "routingFilters": {
                        "instrument_type": str(instrument_type),
                        "user_balance_id": user_balance_id
                    }
                }
            }

        self.send_websocket_request(
            name=main_name, msg=msg, request_id=request_id)

    def set_user_settings(self, balance_id, request_id=""):
        msg = {
            "name": "set-user-settings",
            "version": "1.0",
            "body": {
                "name": "traderoom_gl_common",
                "version": 3,
                "config": {
                    "balanceId": balance_id
                }
            }
        }

        self.send_websocket_request(
            name="sendMessage", msg=msg, request_id=str(request_id))

    def subscribe_position_changed(self, name, instrument_type, request_id):
        # name: position-changed, trading-fx-option.position-changed, digital-options
        # instrument_type: multi-option, crypto, forex, cfd
        msg = {
            "name": name,
            "version": "1.0",
            "params": {
                "routingFilters": {
                    "instrument_type": str(instrument_type)}
            }
        }

        self.send_websocket_request(
            name="subscribeMessage", msg=msg, request_id=str(request_id))

    def set_options(self, request_id, send_results):
        msg = {
            "sendResults": send_results
        }

        self.send_websocket_request(
            name="setOptions", msg=msg, request_id=str(request_id))

    @property
    def subscribe_top_assets_updated(self):
        return SubscribeTopAssetsUpdated(self)

    @property
    def unsubscribe_top_assets_updated(self):
        return UnsubscribeTopAssetsUpdated(self)

    @property
    def subscribe_commission_changed(self):
        return SubscribeCommissionChanged(self)

    @property
    def unsubscribe_commission_changed(self):
        return UnsubscribeCommissionChanged(self)

    @property
    def set_actives(self):
        """Property for get IQ Option websocket setactives channel.

        :returns: The instance of :class:`SetActives <hermes.ws.channels.setactives.SetActives>`.
        """
        return SetActives(self)

    @property
    def get_leader_board(self):
        return LeaderBoard(self)

    @property
    def get_candles(self):
        """Property for get IQ Option websocket candles channel.

        :returns: The instance of :class:`GetCandles
            <hermes.ws.channels.candles.GetCandles>`.
        """
        return GetCandles(self)

    def get_api_option_init_all(self):
        self.send_websocket_request(name="api_option_init_all", msg="")

    def get_api_option_init_all_v2(self):
        msg = {
            "name": "get-initialization-data",
            "version": "3.0",
            "body": {}
        }

        self.send_websocket_request(name="sendMessage", msg=msg)

    @property
    def get_bet_info(self):
        return GameBetInfo(self)

    @property
    def get_options(self):
        return GetOptions(self)

    @property
    def get_options_v2(self):
        return GetOptionsV2(self)

    @property
    def buy_v3(self):
        return BuyV3(self)

    @property
    def buy_by_raw_expired_v3(self):
        return BuyByRawExpiredV3(self)

    @property
    def buy(self):
        """Property for get IQ Option websocket buy v2 request.

        :returns: The instance of :class:`BuyV2 <hermes.ws.channels.buyv2.BuyV2>`.
        """
        self.buy_successful = None

        return BuyV2(self)

    @property
    def sell_option(self):
        return SellOption(self)

    @property
    def sell_digital_option(self):
        return SellDigitalOption(self)

    def get_digital_underlying(self):
        msg = {
            "name": "get-underlying-list",
            "version": "2.0",
            "body": {
                "type": "digital-option"
            }
        }

        self.send_websocket_request(name="sendMessage", msg=msg)

    @property
    def get_strike_list(self):
        return StrikeList(self)

    @property
    def subscribe_instrument_quites_generated(self):
        return Subscribe_Instrument_Quites_Generated(self)

    @property
    def unsubscribe_instrument_quites_generated(self):
        return UnsubscribeInstrumentQuitesGenerated(self)

    @property
    def place_digital_option(self):
        return DigitalOptionsPlaceDigitalOption(self)

    @property
    def close_digital_option(self):
        return DigitalOptionsClosePosition(self)

    @property
    def buy_order(self):
        return BuyPlaceOrderTemp(self)

    @property
    def change_order(self):
        return ChangeTPSL(self)

    @property
    def change_auto_margin_call(self):
        return ChangeAutoMarginCall(self)

    @property
    def get_order(self):
        return GetOrder(self)

    @property
    def get_pending(self):
        return GetDeferredOrders(self)

    @property
    def get_positions(self):
        return GetPositions(self)

    @property
    def get_position(self):
        return GetPosition(self)

    @property
    def get_digital_position(self):
        return GetDigitalPosition(self)

    @property
    def get_position_history(self):
        return GetPositionHistory(self)

    @property
    def get_position_history_v2(self):
        return GetPositionHistoryV2(self)

    @property
    def get_available_leverages(self):
        return GetAvailableLeverages(self)

    @property
    def cancel_order(self):
        return CancelOrder(self)

    @property
    def close_position(self):
        return ClosePosition(self)

    @property
    def get_overnight_fee(self):
        return GetOvernightFee(self)

    @property
    def heartbeat(self):
        return Heartbeat(self)

    def set_session(self, cookies, headers):
        """Method to set session cookies."""
        self.session.headers.update(headers)

        self.session.cookies.clear_session_cookies()
        requests.utils.add_dict_to_cookiejar(self.session.cookies, cookies)

    def start_websocket(self):
        self.check_websocket_if_connect = None
        self.check_websocket_if_error = False
        self.websocket_error_reason = None

        self.websocket_client = WebsocketClient(self)

        self.websocket_thread = threading.Thread(target=self.websocket.run_forever, kwargs={
            "sslopt": {
                "check_hostname": False,
                "cert_reqs": ssl.CERT_NONE,
                "ca_certs": "cacert.pem"
            }})
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        while True:
            try:
                if self.check_websocket_if_error:
                    return False, self.websocket_error_reason
                if self.check_websocket_if_connect == 0:
                    return False, "Websocket connection closed."
                elif self.check_websocket_if_connect == 1:
                    return True, None
            except:
                pass
            pass

    def set_token_sms(self, response):
        token_sms = response.json()['token']
        self.token_sms = token_sms

    def set_token_2fa(self, response):
        token_2fa = response.json()['token']
        self.token_login2fa = token_2fa

    def get_ssid(self):
        response = None

        try:
            if self.token_login2fa is None:
                response = self.login(
                    self.username, self.password)  # pylint: disable=not-callable
            else:
                response = self.login_2fa(
                    self.username, self.password, self.token_login2fa)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(e)
            return e

        return response

    def send_ssid(self):
        self.profile.msg = None

        SSID(self)(self.ssid)

        while self.profile.msg is None:
            pass

        if self.profile.msg == False:
            return False
        else:
            return True

    def connect(self):
        """Method for connection to IQ Option API."""
        self.ssl_mutual_exclusion = False
        self.ssl_mutual_exclusion_write = False

        try:
            self.close()
        except:
            pass

        check_websocket, websocket_reason = self.start_websocket()

        if not check_websocket:
            return check_websocket, websocket_reason

        if self.ssid is not None:
            check_ssid = self.send_ssid()

            if not check_ssid:
                response = self.get_ssid()

                try:
                    self.ssid = response.cookies["ssid"]
                except:
                    return False, response.text

                atexit.register(self.logout)

                self.start_websocket()
                self.send_ssid()
        else:
            response = self.get_ssid()

            try:
                self.ssid = response.cookies["ssid"]
            except:
                self.close()
                return False, response.text

            atexit.register(self.logout)
            self.send_ssid()

        requests.utils.add_dict_to_cookiejar(
            self.session.cookies, {"ssid": self.ssid})

        self.time_sync.server_timestamp = None

        while True:
            try:
                if self.time_sync.server_timestamp is not None:
                    break
            except:
                pass

        return True, None

    def connect2fa(self, sms_code):
        response = self.verify_2fa(sms_code, self.token_sms)

        if response.json()['code'] != 'success':
            return False, response.json()['message']

        self.set_token_2fa(response)

        if self.token_login2fa is None:
            return False, None

        return True, None

    def close(self):
        self.websocket.close()
        self.websocket_thread.join()

    def websocket_alive(self):
        return self.websocket_thread.is_alive()

    @property
    def get_user_profile_client(self):
        return GetUserProfileClient(self)

    @property
    def request_leaderboard_userinfo_deals_client(self):
        return RequestLeaderboardUserinfoDealsClient(self)

    @property
    def get_users_availability(self):
        return GetUsersAvailability(self)
