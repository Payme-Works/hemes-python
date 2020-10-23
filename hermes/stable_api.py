from threading import active_count
import time
import json
import logging
import operator
from collections import defaultdict
from collections import deque
from datetime import datetime, timedelta
from random import randint

from hermes.api import Hermes
import hermes.constants as codes
import hermes.country_id as countries
import hermes.global_value as global_value
from hermes.expiration import get_expiration_time, get_remaning_time


def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))


class StableHermes:
    __version__ = '1.0.0'

    def __init__(self, email, password, balance_mode='PRACTICE'):
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                     3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.email = email
        self.password = password
        self.suspend = 0.5
        self.thread = None
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.subscribe_indicators = []
        self.get_digital_spot_profit_after_sale_data = nested_dict(2, int)
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0

        self.api = None
        self.resp_sms = None

        self.SESSION_HEADER = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/66.0.3359.139 Safari/537.36'
        }
        self.SESSION_COOKIE = {}

        # self.connect()
        # self.change_balance(balance_mode)

    def get_server_timestamp(self):
        return self.api.time_sync.server_timestamp

    def resubscribe_stream(self):
        try:
            for ac in self.subscribe_candle:
                sp = ac.split(',')
                self.start_candles_one_stream(sp[0], sp[1])
        except:
            pass

        try:
            for ac in self.subscribe_candle_all_size:
                self.start_candles_all_size_stream(ac)
        except:
            pass

        try:
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)
        except:
            pass

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    def connect(self, sms_code=None):
        try:
            self.api.close()
        except:
            pass

        self.api = Hermes('iqoption.com', self.email, self.password)
        check = None

        if sms_code is not None:
            self.api.set_token_sms(self.resp_sms)

            status, reason = self.api.connect2fa(sms_code)

            if not status:
                return status, reason

        self.api.set_session(
            headers=self.SESSION_HEADER,
            cookies=self.SESSION_COOKIE
        )

        check, reason = self.api.connect()

        if check:
            self.resubscribe_stream()

            while global_value.balance_id is None:
                pass

            self.position_change_all(
                'subscribeMessage', global_value.balance_id)

            self.order_changed_all('subscribeMessage')
            self.api.set_options(1, True)

            return True, None
        else:
            if json.loads(reason)['code'] == 'verify':
                response = self.api.send_sms_code(json.loads(reason)['token'])

                if response.json()['code'] != 'success':
                    return False, response.json()['message']

                self.resp_sms = response

                return False, '2FA'

            return False, reason

    def connect_2fa(self, sms_code):
        return self.connect(sms_code=sms_code)

    @staticmethod
    def check_connect():
        if global_value.check_websocket_if_connect == 0 or global_value.check_websocket_if_connect is None:
            return False
        else:
            return True

    @staticmethod
    def get_all_actives_opcode():
        return codes.ACTIVES

    def update_actives_opcode(self):
        self.get_all_binary_actives_opcode()
        self.instruments_input_all_in_actives()

        dicc = {}

        for lis in sorted(codes.ACTIVES.items(), key=operator.itemgetter(1)):
            dicc[lis[0]] = lis[1]

        codes.ACTIVES = dicc

    def get_name_by_active_id(self, active_id):
        info = self.get_financial_information(active_id)

        try:
            return info['msg']['data']['active']['name']
        except:
            return None

    def get_financial_information(self, active):
        self.api.financial_information = None
        self.api.get_financial_information(codes.ACTIVES[active])

        while self.api.financial_information is None:
            pass

        return self.api.financial_information

    def get_leader_board(self, country, from_position, to_position, near_traders_count, user_country_id=0,
                         near_traders_country_count=0, top_country_count=0, top_count=0, top_type=2):
        self.api.leaderboard_deals_client = None

        country_id = countries.ID[country]

        self.api.get_leader_board(country_id, user_country_id, from_position, to_position,
                                  near_traders_country_count, near_traders_count, top_country_count, top_count,
                                  top_type)

        while self.api.leaderboard_deals_client is None:
            pass

        return self.api.leaderboard_deals_client

    def get_instruments(self, type):
        time.sleep(self.suspend)
        self.api.instruments = None

        while self.api.instruments is None:
            try:
                self.api.get_instruments(type)
                start = time.time()

                while self.api.instruments is None and time.time() - start < 10:
                    pass
            except:
                logging.error('**error** api.get_instruments need reconnect')
                self.connect()

        return self.api.instruments

    def instruments_input_to_actives(self, type):
        instruments = self.get_instruments(type)

        for ins in instruments['instruments']:
            codes.ACTIVES[ins['id']] = ins['active_id']

    def instruments_input_all_in_actives(self):
        self.instruments_input_to_actives('crypto')
        self.instruments_input_to_actives('forex')
        self.instruments_input_to_actives('cfd')

    def get_all_binary_actives_opcode(self):
        init_info = self.get_all_init()

        for dirr in (['binary', 'turbo']):
            for i in init_info['result'][dirr]['actives']:
                codes.ACTIVES[(init_info['result'][dirr]['actives']
                               [i]['name']).split('.')[1]] = int(i)

    def get_all_init(self):
        while True:
            self.api.api_option_init_all_result = None

            while True:
                try:
                    self.api.get_api_option_init_all()
                    break
                except:
                    logging.error('**error** get_all_init need reconnect')
                    self.connect()
                    time.sleep(5)

            start = time.time()

            while True:
                if time.time() - start > 30:
                    logging.error('**warning** get_all_init late 30 sec')
                    break

                try:
                    if self.api.api_option_init_all_result is not None:
                        break
                except:
                    pass

            try:
                if self.api.api_option_init_all_result['isSuccessful']:
                    return self.api.api_option_init_all_result
            except:
                pass

    def get_all_init_v2(self):
        self.api.api_option_init_all_result_v2 = None

        if not self.check_connect():
            self.connect()

        self.api.get_api_option_init_all_v2()

        start_t = time.time()

        while self.api.api_option_init_all_result_v2 is None:
            if time.time() - start_t >= 30:
                logging.error('**warning** get_all_init_v2 late 30 sec')
                return None

        return self.api.api_option_init_all_result_v2

    def get_all_open_actives(self):
        open_time = nested_dict(3, dict)
        binary_data = self.get_all_init_v2()
        binary_list = ['binary', 'turbo']

        for option in binary_list:
            for actives_id in binary_data[option]['actives']:
                active = binary_data[option]['actives'][actives_id]
                name = str(active['name']).split('.')[1]

                if active['enabled']:
                    if active['is_suspended']:
                        open_time[option][name] = False
                    else:
                        open_time[option][name] = True
                else:
                    open_time[option][name] = active['enabled']

        digital_data = self.get_digital_underlying_list_data()['underlying']

        for digital in digital_data:
            name = digital['underlying']
            schedule = digital['schedule']
            open_time['digital'][name] = False

            for schedule_time in schedule:
                start = schedule_time['open']
                end = schedule_time['close']

                if start < time.time() < end:
                    open_time['digital'][name] = True

        instrument_list = ['cfd', 'forex', 'crypto']

        for instruments_type in instrument_list:
            ins_data = self.get_instruments(instruments_type)['instruments']

            for detail in ins_data:
                name = detail['name']
                schedule = detail['schedule']
                open_time[instruments_type][name] = False

                for schedule_time in schedule:
                    start = schedule_time['open']
                    end = schedule_time['close']
                    if start < time.time() < end:
                        open_time[instruments_type][name] = True

        return open_time

    def get_binary_option_detail(self):
        detail = nested_dict(2, dict)
        init_info = self.get_all_init()

        for actives in init_info['result']['turbo']['actives']:
            name = init_info['result']['turbo']['actives'][actives]['name']
            name = name[name.index('.') + 1:len(name)]
            detail[name]['turbo'] = init_info['result']['turbo']['actives'][actives]

        for actives in init_info['result']['binary']['actives']:
            name = init_info['result']['binary']['actives'][actives]['name']
            name = name[name.index('.') + 1:len(name)]
            detail[name]['binary'] = init_info['result']['binary']['actives'][actives]

        return detail

    def get_all_profit(self):
        all_profit = nested_dict(2, dict)
        init_info = self.get_all_init()

        for actives in init_info['result']['turbo']['actives']:
            name = init_info['result']['turbo']['actives'][actives]['name']
            name = name[name.index('.') + 1:len(name)]
            all_profit[name]['turbo'] = (100.0 - init_info['result']['turbo']['actives'][actives]['option']['profit'][
                'commission']) / 100.0

        for actives in init_info['result']['binary']['actives']:
            name = init_info['result']['binary']['actives'][actives]['name']
            name = name[name.index('.') + 1:len(name)]
            all_profit[name]['binary'] = (100.0 - init_info['result']['binary']['actives'][actives]['option']['profit'][
                'commission']) / 100.0

        return all_profit

    def get_profile_async(self):
        while self.api.profile.msg is None:
            pass

        return self.api.profile.msg

    def get_currency(self):
        balances_raw = self.get_balances()

        for balance in balances_raw['msg']:
            if balance['id'] == global_value.balance_id:
                return balance['currency']

    @staticmethod
    def get_balance_id():
        return global_value.balance_id

    def get_balance(self):

        balances_raw = self.get_balances()
        for balance in balances_raw['msg']:
            if balance['id'] == global_value.balance_id:
                return balance['amount']

    def get_balances(self):
        self.api.balances_raw = None
        self.api.get_balances()

        while self.api.balances_raw is None:
            pass

        if self.api.balances_raw is None:
            return None

        return self.api.balances_raw['msg']

    def get_balance_mode(self):
        profile = self.get_profile_async()

        for balance in profile.get('balances'):
            if balance['id'] == global_value.balance_id:
                if balance['type'] == 1:
                    return 'REAL'
                elif balance['type'] == 4:
                    return 'PRACTICE'
                elif balance['type'] == 2:
                    return 'TOURNAMENT'

    def reset_practice_balance(self):
        self.api.training_balance_reset_request = None
        self.api.reset_training_balance()

        while self.api.training_balance_reset_request is None:
            pass

        return self.api.training_balance_reset_request

    def position_change_all(self, main_name, user_balance_id):
        instrument_type = ['cfd', 'forex', 'crypto',
                           'digital-option', 'turbo-option', 'binary-option']
        for ins in instrument_type:
            self.api.portfolio(main_name=main_name, name='portfolio.position-changed',
                               instrument_type=ins, user_balance_id=user_balance_id)

    def order_changed_all(self, main_name):
        instrument_type = ['cfd', 'forex', 'crypto',
                           'digital-option', 'turbo-option', 'binary-option']
        for ins in instrument_type:
            self.api.portfolio(
                main_name=main_name, name='portfolio.order-changed', instrument_type=ins)

    def change_balance(self, balance_mode):
        def set_id(b_id):
            if global_value.balance_id is not None:
                self.position_change_all(
                    'unsubscribeMessage', global_value.balance_id)

            global_value.balance_id = b_id

            self.position_change_all('subscribeMessage', b_id)

        real_id = None
        practice_id = None
        tournament_id = None

        for balance in self.get_profile_async()['balances']:
            if balance['type'] == 1:
                real_id = balance['id']
            if balance['type'] == 4:
                practice_id = balance['id']
            if balance['type'] == 2:
                tournament_id = balance['id']

        if balance_mode == 'REAL':
            set_id(real_id)
        elif balance_mode == 'PRACTICE':
            set_id(practice_id)
        elif balance_mode == 'TOURNAMENT':
            set_id(tournament_id)
        else:
            logging.error("ERROR doesn't have this mode")
            exit(1)

    def get_candles(self, actives, interval, count, end_time):
        self.api.candles.candles_data = None
        while True:
            try:
                self.api.get_candles(
                    codes.ACTIVES[actives], interval, count, end_time)

                while self.check_connect and self.api.candles.candles_data is None:
                    pass

                if self.api.candles.candles_data is not None:
                    break
            except:
                logging.error('**error** get_candles need reconnect')
                self.connect()

        return self.api.candles.candles_data

    def start_candles_stream(self, active, size, max_dict):
        if size == 'all':
            for s in self.size:
                self.full_realtime_get_candle(active, s, max_dict)
                self.api.real_time_candles_max_dict_table[active][s] = max_dict
            self.start_candles_all_size_stream(active)
        elif size in self.size:
            self.api.real_time_candles_max_dict_table[active][size] = max_dict
            self.full_realtime_get_candle(active, size, max_dict)
            self.start_candles_one_stream(active, size)
        else:
            logging.error(
                '**error** start_candles_stream please input right size')

    def stop_candles_stream(self, active, size):
        if size == 'all':
            self.stop_candles_all_size_stream(active)
        elif size in self.size:
            self.stop_candles_one_stream(active, size)
        else:
            logging.error(
                '**error** start_candles_stream please input right size')

    def get_realtime_candles(self, active, size):
        if size == 'all':
            try:
                return self.api.real_time_candles[active]
            except:
                logging.error(
                    "**error** get_realtime_candles() size='all' can not get candle")

                return False
        elif size in self.size:
            try:
                return self.api.real_time_candles[active][size]
            except:
                logging.error(
                    '**error** get_realtime_candles() size=' + str(size) + ' can not get candle')
                return False
        else:
            logging.error(
                "**error** get_realtime_candles() please input right 'size'")

    def get_all_realtime_candles(self):
        return self.api.real_time_candles

    def full_realtime_get_candle(self, active, size, max_dict):
        candles = self.get_candles(
            active, size, max_dict, self.api.time_sync.server_timestamp)

        for can in candles:
            self.api.real_time_candles[str(
                active)][int(size)][can['from']] = can

    def start_candles_one_stream(self, active, size):
        if not (str(active + ',' + str(size)) in self.subscribe_candle):
            self.subscribe_candle.append((active + ',' + str(size)))

        start = time.time()
        self.api.candle_generated_check[str(active)][int(size)] = {}

        while True:
            if time.time() - start > 20:
                logging.error(
                    '**error** start_candles_one_stream late for 20 sec')
                return False

            try:
                if self.api.candle_generated_check[str(active)][int(size)]:
                    return True
            except:
                pass

            try:
                self.api.subscribe(codes.ACTIVES[active], size)
            except:
                logging.error('**error** start_candles_stream reconnect')
                self.connect()

            time.sleep(1)

    def stop_candles_one_stream(self, active, size):
        if (active + ',' + str(size)) in self.subscribe_candle:
            self.subscribe_candle.remove(active + ',' + str(size))
        while True:
            try:
                if self.api.candle_generated_check[str(active)][int(size)] == {}:
                    return True
            except:
                pass
            self.api.candle_generated_check[str(active)][int(size)] = {}
            self.api.unsubscribe(codes.ACTIVES[active], size)
            time.sleep(self.suspend * 10)

    def start_candles_all_size_stream(self, active):
        self.api.candle_generated_all_size_check[str(active)] = {}

        if not (str(active) in self.subscribe_candle_all_size):
            self.subscribe_candle_all_size.append(str(active))

        start = time.time()

        while True:
            if time.time() - start > 20:
                logging.error('**error** fail ' + active +
                              ' start_candles_all_size_stream late for 10 sec')
                return False

            try:
                if self.api.candle_generated_all_size_check[str(active)]:
                    return True
            except:
                pass

            try:
                self.api.subscribe_all_size(codes.ACTIVES[active])
            except:
                logging.error(
                    '**error** start_candles_all_size_stream reconnect')
                self.connect()

            time.sleep(1)

    def stop_candles_all_size_stream(self, ACTIVE):
        if str(ACTIVE) in self.subscribe_candle_all_size:
            self.subscribe_candle_all_size.remove(str(ACTIVE))

        while True:
            try:
                if self.api.candle_generated_all_size_check[str(ACTIVE)] == {}:
                    break
            except:
                pass

            self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
            self.api.unsubscribe_all_size(codes.ACTIVES[ACTIVE])

            time.sleep(self.suspend * 10)

    def subscribe_top_assets_updated(self, instrument_type):
        self.api.subscribe_top_assets_updated(instrument_type)

    def unsubscribe_top_assets_updated(self, instrument_type):
        self.api.unsubscribe_top_assets_updated(instrument_type)

    def get_top_assets_updated(self, instrument_type):
        if instrument_type in self.api.top_assets_updated_data:
            return self.api.top_assets_updated_data[instrument_type]
        else:
            return None

    def subscribe_commission_changed(self, instrument_type):
        self.api.subscribe_commission_changed(instrument_type)

    def unsubscribe_commission_changed(self, instrument_type):
        self.api.unsubscribe_commission_changed(instrument_type)

    def get_commission_change(self, instrument_type):
        return self.api.subscribe_commission_changed_data[instrument_type]

    def start_mood_stream(self, actives, instrument='turbo-option'):
        if actives not in self.subscribe_mood:
            self.subscribe_mood.append(actives)

        while True:
            self.api.subscribe_traders_mood(
                codes.ACTIVES[actives], instrument)
            try:
                self.api.traders_mood[codes.ACTIVES[actives]]
                break
            except:
                time.sleep(5)

    def stop_mood_stream(self, actives, instrument='turbo-option'):
        if actives in self.subscribe_mood:
            del self.subscribe_mood[actives]
        self.api.unsubscribe_traders_mood(codes.ACTIVES[actives], instrument)

    def get_traders_mood(self, actives):
        return self.api.traders_mood[codes.ACTIVES[actives]]

    def get_all_traders_mood(self):
        return self.api.traders_mood

    def get_technical_indicators(self, actives):
        request_id = self.api.get_technical_indicators(
            codes.ACTIVES[actives])
        while self.api.technical_indicators.get(request_id) is None:
            pass
        return self.api.technical_indicators[request_id]

    def check_binary_order(self, order_id):
        while order_id not in self.api.order_binary:
            pass

        your_order = self.api.order_binary[order_id]

        del self.api.order_binary[order_id]

        return your_order

    def wait_for_order_close(self, order_id):
        while True:
            try:
                return self.api.closed_options[order_id]
            except:
                pass

    def wait_for_result(self, order_id):
        return self.wait_for_order_close(order_id)['result']

    def check_win_old(self, id_number):
        while True:
            try:
                list_info_data_dict = self.api.list_info_data.get(id_number)

                if list_info_data_dict['game_state'] == 1:
                    break
            except:
                pass

        self.api.list_info_data.delete(id_number)

        return list_info_data_dict['win']

    def check_win(self, order_id):
        return self.wait_for_result(order_id) == 'win'

    def check_win_v2(self, id_number, polling_time=1):
        while True:
            check, data = self.get_bet_info(id_number)

            if check:
                win = data['result']['data'][str(id_number)]['win']

                if win != '':
                    try:
                        return data['result']['data'][str(id_number)]['profit'] - data['result']['data'][
                            str(id_number)]['deposit']
                    except IndexError:
                        pass
            else:
                return 0

            time.sleep(polling_time)

    def check_win_v4(self, id_number):
        while True:
            try:
                if self.api.socket_option_closed[id_number] is not None:
                    break
            except IndexError:
                pass

        x = self.api.socket_option_closed[id_number]

        return x['msg']['win'], (
            0 if x['msg']['win'] == 'equal' else float(x['msg']['sum']) * -1 if x['msg']['win'] == 'loose' else float(
                x['msg']['win_amount']) - float(x['msg']['sum']))

    def check_win_v3(self, id_number):
        while True:
            result = self.get_history(10)

            if result['msg']['closed_options'][0]['id'][0] == id_number and result['msg']['closed_options'][0]['id'][
                    0] is not None:
                return result['msg']['closed_options'][0]['win'], (
                    result['msg']['closed_options'][0]['win_amount'] - result['msg']['closed_options'][0]['amount'] if
                    result['msg']['closed_options'][0]['win'] != 'equal' else 0)

            time.sleep(1)

    def get_bet_info(self, id_number):
        while True:
            self.api.game_betinfo.isSuccessful = None

            start = time.time()

            try:
                self.api.get_bet_info(id_number)
            except:
                logging.error(
                    '**error** def get_bet_info  self.api.get_bet_info reconnect')
                self.connect()

            while self.api.game_betinfo.isSuccessful is None:
                if time.time() - start > 10:
                    logging.error(
                        '**error** get_bet_info time out need reconnect')
                    self.connect()
                    self.api.get_bet_info(id_number)
                    time.sleep(self.suspend * 10)
            if self.api.game_betinfo.isSuccessful:
                return self.api.game_betinfo.isSuccessful, self.api.game_betinfo.dict
            else:
                return self.api.game_betinfo.isSuccessful, None

    def get_option_info(self, limit):
        self.api.api_game_get_options_result = None
        self.api.get_options(limit)

        while self.api.api_game_get_options_result is None:
            pass

        return self.api.api_game_get_options_result

    def get_history(self, limit):
        self.api.get_options_v2_data = None
        self.api.get_options_v2(limit, 'digital-option,binary,turbo')

        while self.api.get_options_v2_data is None:
            pass

        binary_history = self.api.get_options_v2_data
        _, digital_history = self.get_position_history_v2(
            'digital-option', limit, 0, 0, 0)

        return {
            'binary': binary_history,
            'digital': digital_history
        }

    def buy_multi(self, price, actives, action, expirations):
        self.api.buy_multi_option = {}

        if len(price) == len(actives) == len(action) == len(expirations):
            buy_len = len(price)

            for idx in range(buy_len):
                self.api.buy_v3(
                    price[idx], codes.ACTIVES[actives[idx]], action[idx], expirations[idx], idx)

            while len(self.api.buy_multi_option) < buy_len:
                pass

            buy_ids = []

            for key in sorted(self.api.buy_multi_option.keys()):
                try:
                    value = self.api.buy_multi_option[str(key)]
                    buy_ids.append(value['id'])
                except:
                    buy_ids.append(None)

            return buy_ids
        else:
            logging.error('buy_multi error please input all same len')

    def get_remaining(self, duration):
        for remaining in get_remaning_time(self.api.time_sync.server_timestamp):
            if remaining[0] == duration:
                return remaining[1]

        logging.error('get_remaning(self,duration) ERROR duration')

        return 'ERROR duration'

    def buy_by_raw_expirations(self, price, active, direction, option, expired):
        self.api.buy_multi_option = {}
        self.api.buy_successful = None

        req_id = 'buyraw'

        try:
            self.api.buy_multi_option[req_id]['id'] = None
        except:
            pass

        self.api.buy_by_raw_expired_v3(
            price, codes.ACTIVES[active], direction, option, expired, request_id=req_id)

        start_t = time.time()
        id = None

        self.api.result = None

        while self.api.result is None or id is None:
            try:
                if 'message' in self.api.buy_multi_option[req_id].keys():
                    logging.error(
                        '**warning** buy' + str(self.api.buy_multi_option[req_id]['message']))
                    return False, self.api.buy_multi_option[req_id]['message']
            except:
                pass

            try:
                id = self.api.buy_multi_option[req_id]['id']
            except:
                pass

            if time.time() - start_t >= 5:
                logging.error('**warning** buy late 5 sec')
                return False, None

        return self.api.result, self.api.buy_multi_option[req_id]['id']

    def buy(self, data):
        """
        Buy a order in some active.

        :param data: {
            type: 'binary' | 'digital';
            active: string;
            price_amount: string;
            action: 'call' | 'put';
            expiration: int;
        }
        """
        typ = data['type']
        active = codes.ACTIVES[data['active']]
        price_amount = float(data['price_amount'])
        action = str(data['action'])
        expiration = int(data['expiration'])

        if typ == 'digital':
            if type(data) is list:
                results = []

                for item in data:
                    buy_result = self.buy_digital_spot(
                        data['active'], price_amount, action, expiration)
                    results.append(buy_result)

                return results

            return self.buy_digital_spot(
                data['active'], price_amount, action, expiration)

        if type(data) is list:
            results = []

            for item in data:
                buy_result = self.buy(item)
                results.append(buy_result)

            return results

        self.api.buy_multi_option = {}
        self.api.buy_successful = None

        req_id = str(randint(0, 10000))

        try:
            self.api.buy_multi_option[req_id]['id'] = None
        except:
            pass

        self.api.buy_v3(price_amount, active, action, expiration, req_id)

        start_t = time.time()
        id = None

        self.api.result = None

        while self.api.result is None or id is None:
            try:
                if 'message' in self.api.buy_multi_option[req_id].keys():
                    return False, self.api.buy_multi_option[req_id]['message']
            except:
                pass

            try:
                id = self.api.buy_multi_option[req_id]['id']
            except:
                pass

            if time.time() - start_t >= 5:
                logging.error('**warning** buy late 5 sec')
                return False, None

        return self.api.result, self.api.buy_multi_option[req_id]['id']

    def sell_option(self, options_id):
        self.api.sell_option(options_id)
        self.api.sold_options_respond = None

        while self.api.sold_options_respond is None:
            pass

        return self.api.sold_options_respond

    def sell_digital_option(self, options_id):
        self.api.sell_digital_option(options_id)
        self.api.sold_digital_options_respond = None

        while self.api.sold_digital_options_respond is None:
            pass

        return self.api.sold_digital_options_respond

    def get_digital_underlying_list_data(self):
        self.api.underlying_list_data = None
        self.api.get_digital_underlying()

        start_t = time.time()

        while self.api.underlying_list_data is None:
            if time.time() - start_t >= 30:
                logging.error(
                    '**warning** get_digital_underlying_list_data late 30 sec')
                return None

        return self.api.underlying_list_data

    def get_strike_list(self, actives, duration):
        self.api.strike_list = None
        self.api.get_strike_list(actives, duration)

        ans = {}

        while self.api.strike_list is None:
            pass

        try:
            for data in self.api.strike_list['msg']['strike']:
                temp = {
                    'call': data['call']['id'],
                    'put': data['put']['id']
                }
                ans[('%.6f' % (float(data['value']) * 10e-7))] = temp
        except:
            logging.error('**error** get_strike_list read problem...')
            return self.api.strike_list, None

        return self.api.strike_list, ans

    def subscribe_strike_list(self, active, expiration_period):
        self.api.subscribe_instrument_quites_generated(
            active, expiration_period)

    def unsubscribe_strike_list(self, active, expiration_period):
        del self.api.instrument_quites_generated_data[active]
        self.api.unsubscribe_instrument_quites_generated(
            active, expiration_period)

    def get_instrument_quites_generated_data(self, active, duration):
        while self.api.instrument_quotes_generated_raw_data[active][duration * 60] == {}:
            pass

        return self.api.instrument_quotes_generated_raw_data[active][duration * 60]

    def get_realtime_strike_list(self, active, duration):
        while True:
            if not self.api.instrument_quites_generated_data[active][duration * 60]:
                pass
            else:
                break

        ans = {}
        now_timestamp = self.api.instrument_quites_generated_timestamp[active][duration * 60]

        while ans == {}:
            if self.get_realtime_strike_list_temp_data == {} \
                    or now_timestamp != self.get_realtime_strike_list_temp_expiration:
                raw_data, strike_list = self.get_strike_list(active, duration)
                self.get_realtime_strike_list_temp_expiration = raw_data['msg']['expiration']
                self.get_realtime_strike_list_temp_data = strike_list
            else:
                strike_list = self.get_realtime_strike_list_temp_data

            profit = self.api.instrument_quites_generated_data[active][duration * 60]

            for price_key in strike_list:
                try:
                    side_data = {}

                    for side_key in strike_list[price_key]:
                        detail_data = {}
                        profit_d = profit[strike_list[price_key][side_key]]
                        detail_data['profit'] = profit_d
                        detail_data['id'] = strike_list[price_key][side_key]
                        side_data[side_key] = detail_data

                    ans[price_key] = side_data
                except:
                    pass

        return ans

    def get_binary_active_profit(self, active, duration):
        instrument = 'turbo'

        if duration >= 5:
            instrument = 'binary'

        data = self.get_all_init_v2()

        for active_id in data[instrument]['actives']:
            active_data = data[instrument]['actives'][active_id]
            name = active_data['name'].replace('/', '')

            if name == f'front.{active}':
                commission = active_data['option']['profit']['commission']

                return 100 - commission

        return -1

    def get_digital_active_profit(self, active, duration):
        self.subscribe_strike_list(active, duration)

        profit = self.api.instrument_quites_generated_data[active][duration * 60]

        while len(profit) == 0:
            profit = self.api.instrument_quites_generated_data[active][duration * 60]
            pass

        self.unsubscribe_strike_list(active, duration)

        for key in profit:
            if key.find('SPT') != -1:
                return int(format(profit[key], '.0f'))

        return -1

    def buy_digital_spot(self, active, amount, action, duration):
        # Expiration time need to be formatted like this: YYYYMMDDHHII
        # And need to be on GMT time
        if action == 'put':
            action = 'P'
        elif action == 'call':
            action = 'C'
        else:
            logging.error('buy_digital_spot active error')
            return -1

        timestamp = int(self.api.time_sync.server_timestamp)

        if duration == 1:
            exp, _ = get_expiration_time(timestamp, duration)
        else:
            now_date = datetime.fromtimestamp(
                timestamp) + timedelta(minutes=1, seconds=30)

            while True:
                if now_date.minute % duration == 0 and time.mktime(now_date.timetuple()) - timestamp > 30:
                    break
                now_date = now_date + timedelta(minutes=1)

            exp = time.mktime(now_date.timetuple())

        date_formatted = str(datetime.utcfromtimestamp(
            exp).strftime('%Y%m%d%H%M'))
        instrument_id = 'do' + active + date_formatted + \
            'PT' + str(duration) + 'M' + action + 'SPT'

        request_id = self.api.place_digital_option(instrument_id, amount)

        while self.api.digital_option_placed_id.get(request_id) is None:
            pass

        digital_order_id = self.api.digital_option_placed_id.get(request_id)

        if isinstance(digital_order_id, int):
            return True, digital_order_id
        else:
            return False, digital_order_id

    def get_digital_spot_profit_after_sale(self, position_id):
        def get_instrument_id_to_bid(data, instrument_id):
            for row in data['msg']['quotes']:
                if row['symbols'][0] == instrument_id:
                    return row['price']['bid']
            return None

        while self.get_async_order(position_id)['position-changed'] == {}:
            pass

        position = self.get_async_order(position_id)['position-changed']['msg']

        if position['instrument_id'].find('MPSPT'):
            z = False
        elif position['instrument_id'].find('MCSPT'):
            z = True
        else:
            logging.error(
                'get_digital_spot_profit_after_sale position error' + str(position['instrument_id']))

        actives = position['raw_event']['instrument_underlying']
        amount = max(position['raw_event']['buy_amount'],
                     position['raw_event']['sell_amount'])
        start_duration = position['instrument_id'].find('PT') + 2
        end_duration = start_duration + \
            position['instrument_id'][start_duration:].find('M')

        duration = int(position['instrument_id'][start_duration:end_duration])
        z2 = False

        get_abs_count = position['raw_event']['count']
        instrument_strike_value = position['raw_event']['instrument_strike_value'] / 1000000.0
        spot_lower_instrument_strike = position['raw_event']['extra_data']['lower_instrument_strike'] / 1000000.0
        spot_upper_instrument_strike = position['raw_event']['extra_data']['upper_instrument_strike'] / 1000000.0

        a_var = position['raw_event']['extra_data']['lower_instrument_id']
        a_var2 = position['raw_event']['extra_data']['upper_instrument_id']
        get_rate = position['raw_event']['currency_rate']

        instrument_quites_generated_data = self.get_instrument_quites_generated_data(
            actives, duration)

        f_tmp = get_instrument_id_to_bid(
            instrument_quites_generated_data, a_var)

        if f_tmp is not None:
            self.get_digital_spot_profit_after_sale_data[position_id]['f'] = f_tmp
            f = f_tmp
        else:
            f = self.get_digital_spot_profit_after_sale_data[position_id]['f']

        f2_tmp = get_instrument_id_to_bid(
            instrument_quites_generated_data, a_var2)

        if f2_tmp is not None:
            self.get_digital_spot_profit_after_sale_data[position_id]['f2'] = f2_tmp
            f2 = f2_tmp
        else:
            f2 = self.get_digital_spot_profit_after_sale_data[position_id]['f2']

        if (spot_lower_instrument_strike != instrument_strike_value) and f is not None and f2 is not None:

            if (spot_lower_instrument_strike > instrument_strike_value or instrument_strike_value > spot_upper_instrument_strike):
                if z:
                    instrument_strike_value = (spot_upper_instrument_strike - instrument_strike_value) / abs(
                        spot_upper_instrument_strike - spot_lower_instrument_strike)
                    f = abs(f2 - f)
                else:
                    instrument_strike_value = (instrument_strike_value - spot_upper_instrument_strike) / abs(
                        spot_upper_instrument_strike - spot_lower_instrument_strike)
                    f = abs(f2 - f)

            elif z:
                f += ((instrument_strike_value - spot_lower_instrument_strike) /
                      (spot_upper_instrument_strike - spot_lower_instrument_strike)) * (f2 - f)
            else:
                instrument_strike_value = (spot_upper_instrument_strike - instrument_strike_value) / (
                    spot_upper_instrument_strike - spot_lower_instrument_strike)
                f -= f2
            f = f2 + (instrument_strike_value * f)

        if z2:
            pass
        if f is not None:
            price = (f / get_rate)
            return price * get_abs_count - amount
        else:
            return None

    def buy_digital(self, amount, instrument_id):
        self.api.digital_option_placed_id = None
        self.api.place_digital_option(instrument_id, amount)

        start_t = time.time()

        while self.api.digital_option_placed_id is None:
            if time.time() - start_t > 30:
                logging.error('buy_digital loss digital_option_placed_id')
                return False, None

        return True, self.api.digital_option_placed_id

    def close_digital_option(self, position_id):
        self.api.result = None

        while self.get_async_order(position_id)['position-changed'] == {}:
            pass

        position_changed = self.get_async_order(
            position_id)['position-changed']['msg']
        self.api.close_digital_option(position_changed['external_id'])

        while self.api.result is None:
            pass

        return self.api.result

    def check_win_digital(self, buy_order_id, polling_time):
        while True:
            time.sleep(polling_time)
            data = self.get_digital_position(buy_order_id)

            if data['msg']['position']['status'] == 'closed':
                if data['msg']['position']['close_reason'] == 'default':
                    return data['msg']['position']['pnl_realized']
                elif data['msg']['position']['close_reason'] == 'expired':
                    return data['msg']['position']['pnl_realized'] - data['msg']['position']['buy_amount']

    def check_win_digital_v2(self, buy_order_id):
        while self.get_async_order(buy_order_id)['position-changed'] == {}:
            pass

        order_data = self.get_async_order(
            buy_order_id)['position-changed']['msg']

        if order_data is not None:
            if order_data['status'] == 'closed':
                if order_data['close_reason'] == 'expired':
                    return True, order_data['close_profit'] - order_data['invest']
                elif order_data['close_reason'] == 'default':
                    return True, order_data['pnl_realized']
            else:
                return False, None
        else:
            return False, None

    def buy_order(self,
                  instrument_type, instrument_id,
                  side, amount, leverage,
                  type, limit_price=None, stop_price=None,
                  stop_lose_kind=None, stop_lose_value=None,
                  take_profit_kind=None, take_profit_value=None,
                  use_trail_stop=False, auto_margin_call=False,
                  use_token_for_commission=False):
        self.api.buy_order_id = None
        self.api.buy_order(
            instrument_type=instrument_type, instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price, stop_price=stop_price,
            stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
            take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
            use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission
        )
        while self.api.buy_order_id is None:
            pass

        check, data = self.get_order(self.api.buy_order_id)

        while data['status'] == 'pending_new':
            check, data = self.get_order(self.api.buy_order_id)
            time.sleep(1)

        if check:
            if data['status'] != 'rejected':
                return True, self.api.buy_order_id
            else:
                return False, data['reject_status']
        else:

            return False, None

    def change_auto_margin_call(self, id_name, id, auto_margin_call):
        self.api.auto_margin_call_changed_respond = None
        self.api.change_auto_margin_call(id_name, id, auto_margin_call)

        while self.api.auto_margin_call_changed_respond is None:
            pass

        if self.api.auto_margin_call_changed_respond['status'] == 2000:
            return True, self.api.auto_margin_call_changed_respond
        else:
            return False, self.api.auto_margin_call_changed_respond

    def change_order(self, id_name, order_id,
                     stop_lose_kind, stop_lose_value,
                     take_profit_kind, take_profit_value,
                     use_trail_stop, auto_margin_call):
        check = True

        if id_name == 'position_id':
            check, order_data = self.get_order(order_id)
            position_id = order_data['position_id']
            change_order_id = position_id
        elif id_name == 'order_id':
            change_order_id = order_id
        else:
            logging.error('change_order input error ID_Name')

        if check:
            self.api.tpsl_changed_respond = None
            self.api.change_order(
                id_name=id_name, ID=change_order_id,
                stop_lose_kind=stop_lose_kind, stop_lose_value=stop_lose_value,
                take_profit_kind=take_profit_kind, take_profit_value=take_profit_value,
                use_trail_stop=use_trail_stop)
            self.change_auto_margin_call(
                id_name=id_name, id=change_order_id, auto_margin_call=auto_margin_call)

            while self.api.tpsl_changed_respond is None:
                pass

            if self.api.tpsl_changed_respond['status'] == 2000:
                return True, self.api.tpsl_changed_respond['msg']
            else:
                return False, self.api.tpsl_changed_respond
        else:
            logging.error('change_order fail to get position_id')
            return False, None

    def get_async_order(self, buy_order_id):
        return self.api.order_async[buy_order_id]

    def get_order(self, buy_order_id):
        # reject: you can not get this order
        # pending_new: this order is working now
        # filled: this order is ok now
        self.api.order_data = None
        self.api.get_order(buy_order_id)

        while self.api.order_data is None:
            pass

        if self.api.order_data['status'] == 2000:
            return True, self.api.order_data['msg']
        else:
            return False, None

    def get_pending(self, instrument_type):
        self.api.deferred_orders = None
        self.api.get_pending(instrument_type)

        while self.api.deferred_orders is None:
            pass

        if self.api.deferred_orders['status'] == 2000:
            return True, self.api.deferred_orders['msg']
        else:
            return False, None

    def get_positions(self, instrument_type):
        self.api.positions = None
        self.api.get_positions(instrument_type)

        while self.api.positions is None:
            pass

        if self.api.positions['status'] == 2000:
            return True, self.api.positions['msg']
        else:
            return False, None

    def get_position(self, buy_order_id):
        self.api.position = None
        check, order_data = self.get_order(buy_order_id)
        position_id = order_data['position_id']
        self.api.get_position(position_id)

        while self.api.position is None:
            pass

        if self.api.position['status'] == 2000:
            return True, self.api.position['msg']
        else:
            return False, None

    def get_digital_position_by_position_id(self, position_id):
        '''Heavy function. Be careful!'''
        self.api.position = None
        self.api.get_digital_position(position_id)

        while self.api.position is None:
            pass

        return self.api.position

    def get_digital_position(self, order_id):
        self.api.position = None

        while self.get_async_order(order_id)['position-changed'] == {}:
            pass

        position_id = self.get_async_order(
            order_id)['position-changed']['msg']['external_id']

        self.api.get_digital_position(position_id)

        while self.api.position is None:
            pass

        return self.api.position

    def get_position_history(self, instrument_type):
        self.api.position_history = None
        self.api.get_position_history(instrument_type)

        while self.api.position_history is None:
            pass

        if self.api.position_history['status'] == 2000:
            return True, self.api.position_history['msg']
        else:
            return False, None

    def get_position_history_v2(self, instrument_type, limit, offset, start, end):
        # instrument_type: crypto, forex, fx-option, multi-option, cfd, digital-option, turbo-option
        self.api.position_history_v2 = None
        self.api.get_position_history_v2(
            instrument_type, limit, offset, start, end)

        while self.api.position_history_v2 is None:
            pass

        if self.api.position_history_v2['status'] == 2000:
            return True, self.api.position_history_v2['msg']
        else:
            return False, None

    def get_available_leverages(self, instrument_type, actives=''):
        self.api.available_leverages = None

        if actives == '':
            self.api.get_available_leverages(instrument_type, '')
        else:
            self.api.get_available_leverages(
                instrument_type, codes.ACTIVES[actives])

        while self.api.available_leverages is None:
            pass

        if self.api.available_leverages['status'] == 2000:
            return True, self.api.available_leverages['msg']
        else:
            return False, None

    def cancel_order(self, buy_order_id):
        self.api.order_canceled = None
        self.api.cancel_order(buy_order_id)

        while self.api.order_canceled is None:
            pass

        if self.api.order_canceled['status'] == 2000:
            return True
        else:
            return False

    def close_position(self, position_id):
        check, data = self.get_order(position_id)

        if data['position_id'] is not None:
            self.api.close_position_data = None
            self.api.close_position(data['position_id'])

            while self.api.close_position_data is None:
                pass
            if self.api.close_position_data['status'] == 2000:
                return True
            else:
                return False
        else:
            return False

    def close_position_v2(self, position_id):
        while self.get_async_order(position_id) is None:
            pass

        position_changed = self.get_async_order(position_id)
        self.api.close_position(position_changed['id'])

        while self.api.close_position_data is None:
            pass

        if self.api.close_position_data['status'] == 2000:
            return True
        else:
            return False

    def get_overnight_fee(self, instrument_type, active):
        self.api.overnight_fee = None
        self.api.get_overnight_fee(instrument_type, codes.ACTIVES[active])

        while self.api.overnight_fee is None:
            pass

        if self.api.overnight_fee['status'] == 2000:
            return True, self.api.overnight_fee['msg']
        else:
            return False, None

    def get_option_open_by_other_pc(self):
        return self.api.socket_option_opened

    def del_option_open_by_other_pc(self, id):
        del self.api.socket_option_opened[id]

    @staticmethod
    def opcode_to_name(opcode):
        return list(codes.ACTIVES.keys())[list(codes.ACTIVES.values()).index(opcode)]

    def subscribe_live_deal(self, name, active, _type, buffersize):
        # name: live-deal-binary-option-placed, live-deal-digital-option
        active_id = codes.ACTIVES[active]

        self.api.subscribe_live_deal(name, active_id, _type)

    def unsubscribe_live_deal(self, name, active, _type):
        active_id = codes.ACTIVES[active]
        self.api.unsubscribe_live_deal(name, active_id, _type)

    def set_digital_live_deal_cb(self, cb):
        self.api.digital_live_deal_cb = cb

    def set_binary_live_deal_cb(self, cb):
        self.api.binary_live_deal_cb = cb

    def get_live_deal(self, name, active, _type):
        return self.api.live_deal_data[name][active][_type]

    def pop_live_deal(self, name, active, _type):
        return self.api.live_deal_data[name][active][_type].pop()

    def clear_live_deal(self, name, active, _type, buffersize):
        self.api.live_deal_data[name][active][_type] = deque(
            list(), buffersize)

    def get_user_profile_client(self, user_id):
        self.api.user_profile_client = None
        self.api.get_user_profile_client(user_id)

        while self.api.user_profile_client is None:
            pass

        return self.api.user_profile_client

    def request_leaderboard_userinfo_deals_client(self, user_id, country_id):
        self.api.leaderboard_userinfo_deals_client = None

        while True:
            try:
                if self.api.leaderboard_userinfo_deals_client['isSuccessful']:
                    break
            except:
                pass

            self.api.request_leaderboard_userinfo_deals_client(
                user_id, country_id)
            time.sleep(0.2)

        return self.api.leaderboard_userinfo_deals_client

    def get_users_availability(self, user_id):
        self.api.users_availability = None

        while self.api.users_availability is None:
            self.api.get_users_availability(user_id)
            time.sleep(0.2)

        return self.api.users_availability
