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
    GAP_FILL,
    LEVERAGE,
    POSITION_SIZE_DIAPASON,
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
    check_trade_condition,
    calc_slippage_percentage
)
from modules.utils.smart_sleep import smart_sleep

from modules.patterns import Singleton
from collections import deque
import keyboard
import time
from modules.structs.side import Side


class TradingAlgorithm(Singleton):
    def __init__(self):
        self.run_flag = True
        self.close_flag = False

        self.mexc_service = MexcService()
        self.dex_parser = DexToolsParser()

        self.mexc_last_price = None
        self.dex_last_price = None

        self.mexc_prices = deque()
        self.dex_prices = deque()

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
        logger.info('Trading algorithm stopping...')

        self.mexc_service.driver_service.close_driver()
        self.dex_parser.driver_service.close_driver()
        logger.info('Trading algorithm stopped')
        self.close_flag = True

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

            trade_info = check_trade_condition(self.dex_prices, self.mexc_prices,
                                               self.dex_last_price, self.mexc_last_price)

            if not trade_info:
                smart_sleep(start_time, LOOP_DELAY)
                continue

            side = trade_info['side']
            position_size = trade_info['position_size']

            self.mexc_service.open_position(side, position_size)

            while self.mexc_service.is_active_orders():
                logger.debug('Waiting for order to be filled.')

            enter_price = self.mexc_service.get_enter_price()
            tp_limit = calc_tp_limit(side, self.dex_last_price, enter_price, GAP_FILL, DECIMALS)
            slippage_percentage = calc_slippage_percentage(enter_price, self.mexc_last_price)

            percentage_profit_with_leverage = calc_percent_profit_with_leverage(
                side, enter_price, tp_limit, LEVERAGE)

            self.mexc_service.set_tp_by_limit(tp_limit)

            logger.info(f'Position opened. Side: {side}, Position size: {position_size}, '
                        f'Enter price: {enter_price}, TP limit: {tp_limit}, Slippage: {slippage_percentage}',
                        f'DEX price: {self.dex_last_price}, MEXC price: {self.mexc_last_price}',
                        f'Percentage profit with leverage: {percentage_profit_with_leverage}')

            send_position_info_message_to_telegram(
                side=side,
                position_size=position_size,
                enter_price=enter_price,
                tp_limit=tp_limit,
                slippage_percentage=slippage_percentage,
                dex_price=self.dex_last_price,
                mexc_price=self.mexc_last_price,
                percentage_profit_with_leverage=percentage_profit_with_leverage,
            )

            self.control_position(side, enter_price, tp_limit)

    def control_position(self, side: Side, enter_price: float, tp_limit: float):
        while self.mexc_service.is_active_orders():
            start_time = time.time()

            self.update_prices()

            if (self.dex_last_price > enter_price and side == Side.SHORT) or \
               (self.dex_last_price < enter_price and side == Side.LONG):

                self.mexc_service.close_active_order_by_market()
                logger.info(f'Position closed by market order. Side: {side}, Enter price: {enter_price}, '
                            f'DEX price: {self.dex_last_price} MEXC price: {self.mexc_last_price}')

                send_position_closed_message_to_telegram(
                    enter_price=enter_price,
                    mexc_price=self.mexc_last_price,
                    dex_price=self.dex_last_price
                )

                time.sleep(5)
                break

            new_tp_limit = calc_tp_limit(side,  self.dex_last_price,
                                         enter_price, GAP_FILL, DECIMALS)

            tp_diff = abs(tp_limit - new_tp_limit) / tp_limit * 100

            if tp_diff < TP_CHANGE_THRESHOLD:
                smart_sleep(start_time, LOOP_DELAY)
                continue  # Skip updating TP if change is below threshold

            tp_limit = new_tp_limit
            self.mexc_service.close_any_limit_orders()
            self.mexc_service.set_tp_by_limit(tp_limit)
            logger.info('Take profit price updated.')

            percentage_profit_with_leverage = calc_percent_profit_with_leverage(
                side, enter_price, tp_limit, LEVERAGE)

            send_new_tp_limit_message_to_telegram(
                tp_limit=tp_limit,
                dex_price=self.dex_last_price,
                mexc_price=self.mexc_last_price,
                percentage_profit_with_leverage=percentage_profit_with_leverage,
            )

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

        logger.debug(f'MEXC price: {mexc_price} |---| DEX price: {dex_price}')