import re

from .driver_service import DriverService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from data.driver.queries import *
from modules.utils.logger_loader import logger

from modules.utils.selenium_utils import find_element_with_wait, extract_order_count
from modules.patterns import Singleton
from modules.structs.side import Side

from data.urls import MEXC_FUTURES_COIN_URL
from data.config import POSITION_SIZE


class MexcService(Singleton):
    def __init__(self):
        self.driver_service = DriverService(startup_page=MEXC_FUTURES_COIN_URL, use_cookies=True)
        self.driver = self.driver_service.get_driver()

    def set_position_size(self, size: float) -> None:
        try:
            position_input = find_element_with_wait(self.driver, MEXC_INPUT_POSITION_SIZE)
            position_input.clear()
            position_input.send_keys(str(size))
            logger.info(f"Position size set to {size}.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Position input not found.')
            raise e

    def get_enter_price(self) -> float:
        try:
            enter_price_span = self.driver.find_element(By.XPATH, MEXC_ENTER_PRICE_SPAN)

            enter_price_str = enter_price_span.text
            enter_price = float(enter_price_str.replace(',', '.'))

            return enter_price
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Enter price not found.')
            raise e

    def set_tp_by_limit(self, tp_limit_price: float) -> None:
        try:
            price_input = find_element_with_wait(self.driver, MEXC_TP_LIMIT_PRICE_INPUT)
            price_input.clear()
            price_input.send_keys(str(tp_limit_price))

            size_input = find_element_with_wait(self.driver, MEXC_TP_LIMIT_SIZE_INPUT)
            size_input.clear()
            size_input.send_keys(str(10000))

            close_btn = find_element_with_wait(self.driver, MEXC_TP_LIMIT_CLOSE_BUTTON)
            close_btn.click()

            logger.info(f"Set take profit limit order at price {tp_limit_price}.")

        except (NoSuchElementException, TimeoutException) as e:
            logger.error(f"An error occurred while setting TP by limit: {e}")
            raise e

    def close_any_limit_orders(self):
        try:
            open_orders_tab_button = find_element_with_wait(self.driver, MEXC_OPEN_ORDERS_TAB_BTN)
            num_of_all_orders = extract_order_count(open_orders_tab_button.text)

            if num_of_all_orders == 0:
                logger.info("No open orders found.")
                return

            open_orders_tab_button.click()

            limit_orders_tab_button = find_element_with_wait(self.driver, MEXC_LIMIT_ORDER_TAB)
            num_of_limit_orders = extract_order_count(limit_orders_tab_button.text)

            if num_of_limit_orders == 0:
                logger.info("No limit orders to close.")
                return

            limit_orders_tab_button.click()

            close_all_limits_orders_button = find_element_with_wait(self.driver, MEXC_CLOSE_ALL_LIMITS_ORDERS)
            close_all_limits_orders_button.click()

            confirm_button = find_element_with_wait(self.driver, MEXC_CLOSE_ALL_LIMITS_ORDER_CONFIRM_BTN)
            confirm_button.click()

            logger.info(f"Closed {num_of_limit_orders} limit orders.")

        except (NoSuchElementException, TimeoutException) as e:
            logger.error(f"An error occurred while closing limit orders: {e}")
            raise e

        finally:
            try:
                open_positions_tab_button = find_element_with_wait(self.driver, MEXC_OPEN_POSITIONS_TAB_BTN)
                open_positions_tab_button.click()
            except (NoSuchElementException, TimeoutException) as e:
                logger.error(f"Could not navigate back to open positions tab: {e}")
                raise e

    def close_active_order_by_market(self):
        try:
            fast_close_btn = find_element_with_wait(self.driver, MEXC_FAST_CLOSE_POSITION_BTN)
            fast_close_btn.click()
            logger.info("Closed active order by market.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Fast close button not found.')
            raise e

    def click_open_order_button(self, side: Side) -> None:
        try:
            if side == Side.LONG:
                open_order_btn_xpath = MEXC_OPEN_LONG_POSITION_BTN
            else:
                open_order_btn_xpath = MEXC_OPEN_SHORT_POSITION_BTN

            open_order_btn = find_element_with_wait(self.driver, open_order_btn_xpath)
            open_order_btn.click()
            logger.info(f"Clicked open order button for side {side.name}.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Open order button not found.')
            raise e

    def is_active_orders(self) -> bool:
        try:
            element_text = find_element_with_wait(self.driver, MEXC_OPEN_POSITIONS_TAB_BTN).text
            num_of_orders = extract_order_count(element_text)
            has_orders = num_of_orders > 0
            logger.info(f"Active orders exist: {has_orders}")
            return has_orders
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Open positions tab not found.')
            raise e

    def open_position(self, side: Side) -> None:
        try:
            self.set_position_size(POSITION_SIZE)
            self.click_open_order_button(side)
        except Exception as e:
            logger.error(f"An error occurred while opening position: {e}")
            raise e
