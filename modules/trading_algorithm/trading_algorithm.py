from modules.services.mexc_service import MexcService
from modules.services.dex_parser_serivce import DexToolsParser

from modules.utils.logger_loader import logger
from modules.utils.telegram_logs import (
    send_new_tp_limit_message_to_telegram,
    send_position_info_message_to_telegram,
    send_position_closed_message_to_telegram
)

from modules.utils.mexc_utils import parse_price_mexc_futures
from data.config import (
    MEXC_NAME_COIN,
    MAX_LOOKBACK_TIME_SECONDS,
    MIN_PRICE_CHANGE_DEX,
    MIN_PRICE_DIFFERENCE_PERCENTAGE,
    GAP_FILL,
    LEVERAGE,
    POSITION_SIZE,
    TP_CHANGE_THRESHOLD,
    LOOP_DELAY,
    DECIMALS
)

from modules.utils.trading_algorithm_utils import (
    get_max_price_change_percentage,
    get_corresponding_price_change_percentage,
    clear_deque_prices,
    calc_tp_limit,
    calc_percent_profit_with_leverage,
)
from modules.utils.smart_sleep import smart_sleep

from modules.patterns import Singleton
from collections import deque
import keyboard
import time
from modules.structs.side import Side


class TradingAlgorithm(Singleton):
    def __init__(self):
        self.run_flag = False
        self.close_flag = False
        self.start_trade_working = False

        self.mexc_service = MexcService()
        self.dex_parser = DexToolsParser()

        self.mexc_last_price = None
        self.dex_last_price = None

        self.mexc_prices = deque()
        self.dex_prices = deque()

        self.trade_side = None
        self._add_keybinds()

    def _add_keybinds(self):
        keyboard.add_hotkey('ctrl+shift+s', self._start)
        keyboard.add_hotkey('ctrl+shift+p', self._pause)
        keyboard.add_hotkey('ctrl+shift+q', self._stop)
        keyboard.add_hotkey('ctrl+shift+e', self._save_cookies)

    def _save_cookies(self):
        self.mexc_service.driver_service.save_cookies()
        self.dex_parser.driver_service.save_cookies()

    def _start(self):
        if self.run_flag:
            return

        self.run_flag = True
        logger.info('Trading algorithm started')

    def _pause(self):
        if not self.run_flag:
            return

        self.run_flag = False
        logger.info('Trading algorithm paused')

    def _stop(self):
        self._pause()

        self.mexc_service.driver_service.close_driver()
        self.dex_parser.driver_service.close_driver()

        self.close_flag = True
        logger.info('Trading algorithm stopped')

    def start_trade(self):
        while not self.close_flag:
            start_time = time.time()

            if not self.run_flag:
                smart_sleep(start_time, LOOP_DELAY)
                continue

            self.update_prices()

            if self.mexc_service.is_active_orders():
                smart_sleep(start_time, LOOP_DELAY)
                continue

            if not self.check_trade_condition():
                smart_sleep(start_time, LOOP_DELAY)
                continue

            self.mexc_service.open_position(self.trade_side)

            while self.mexc_service.is_active_orders():
                logger.debug('Waiting for order to be filled.')

            enter_price = self.mexc_service.get_enter_price()
            enter_price_rounded = round(enter_price, DECIMALS)
            tp_limit = calc_tp_limit(self.trade_side, self.dex_last_price, enter_price, GAP_FILL, DECIMALS)

            percentage_profit_with_leverage = calc_percent_profit_with_leverage(
                self.trade_side, enter_price, tp_limit, LEVERAGE)
            self.mexc_service.set_tp_by_limit(tp_limit)

            send_position_info_message_to_telegram(
                side=self.trade_side,
                position_size=POSITION_SIZE,
                enter_price=enter_price_rounded,
                tp_limit=tp_limit,
                dex_price=self.dex_last_price,
                mexc_price=self.mexc_last_price,
                percentage_profit_with_leverage=percentage_profit_with_leverage,
            )

            self.control_position(self.trade_side, enter_price, tp_limit)

    def control_position(self, side: Side, enter_price: float, tp_limit: float):
        while self.mexc_service.is_active_orders():
            start_time = time.time()

            self.update_prices()

            if (self.dex_last_price > enter_price and side == Side.SHORT) or \
               (self.dex_last_price < enter_price and side == Side.LONG):
                self.mexc_service.close_active_order_by_market()
                logger.info('Position closed by market due to adverse price movement.')
                send_position_closed_message_to_telegram(
                    enter_price=enter_price,
                    mexc_price=self.mexc_last_price,
                    dex_price=self.dex_last_price
                )
                time.sleep(5)
                break

            new_tp_limit = calc_tp_limit(side, self.dex_last_price, enter_price, GAP_FILL, DECIMALS)
            tp_diff = abs(tp_limit - new_tp_limit) / tp_limit * 100

            if tp_diff < TP_CHANGE_THRESHOLD:
                smart_sleep(start_time, LOOP_DELAY)
                continue  # Skip updating TP if change is below threshold

            tp_limit = new_tp_limit
            self.mexc_service.close_any_limit_orders()
            self.mexc_service.set_tp_by_limit(tp_limit)
            logger.info('Take profit price updated.')

            percentage_profit_with_leverage = calc_percent_profit_with_leverage(
                self.trade_side, enter_price, tp_limit, LEVERAGE)

            send_new_tp_limit_message_to_telegram(
                tp_limit=tp_limit,
                dex_price=self.dex_last_price,
                mexc_price=self.mexc_last_price,
                percentage_profit_with_leverage=percentage_profit_with_leverage,
            )

    def check_trade_condition(self):
        dex_price_change_info = get_max_price_change_percentage(self.dex_prices)

        if dex_price_change_info is None:
            return False

        if MIN_PRICE_CHANGE_DEX > dex_price_change_info["max_diff_percentage"]:
            logger.debug(f'Max price change on DEX {dex_price_change_info["max_diff_percentage"]}% is less than {MIN_PRICE_CHANGE_DEX}%, skipping.')
            return False

        mexc_price_change_percentage = get_corresponding_price_change_percentage(
            self.mexc_prices, dex_price_change_info["timestamp"])

        if mexc_price_change_percentage is None:
            logger.debug('No corresponding price change in MEXC, skipping.')
            return False

        if abs(mexc_price_change_percentage) >= abs(dex_price_change_info["max_diff_percentage"]):
            logger.debug(f'Price change on MEXC {mexc_price_change_percentage}% is greater than on DEX {dex_price_change_info["max_diff_percentage"]}%, skipping.')
            return False

        price_difference_percentage = (self.dex_last_price - self.mexc_last_price) / self.dex_last_price * 100

        logger.debug(f'Price difference between DEX and MEXC: {price_difference_percentage:.2f}%')

        if abs(price_difference_percentage) < MIN_PRICE_DIFFERENCE_PERCENTAGE:
            logger.debug('Price movement direction does not match, skipping.')
            return False

        self.trade_side = Side.LONG if price_difference_percentage > 0 else Side.SHORT
        return True

    def update_prices(self):
        now_time = time.time()
        mexc_price = parse_price_mexc_futures(MEXC_NAME_COIN)
        dex_price = self.dex_parser.get_price()

        if not mexc_price or not dex_price:
            logger.error('Error while parsing prices')
            return

        self.mexc_prices = clear_deque_prices(self.mexc_prices, MAX_LOOKBACK_TIME_SECONDS, now_time)
        self.dex_prices = clear_deque_prices(self.dex_prices, MAX_LOOKBACK_TIME_SECONDS, now_time)

        mexc_price = round(mexc_price, DECIMALS)
        dex_price = round(dex_price, DECIMALS)

        self.mexc_prices.append((now_time, mexc_price))
        self.dex_prices.append((now_time, dex_price))

        self.mexc_last_price = mexc_price
        self.dex_last_price = dex_price

        logger.debug(f'MEXC price: {mexc_price} | DEX price: {dex_price}')
