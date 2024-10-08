from modules.services.driver_service import DriverService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from data.driver.driver_config import OPTIONS_ARGS
from selenium.webdriver.common.by import By

from modules.patterns import Singleton
from data.urls import DEX_COIN_URL
from data.driver.queries import DEX_TOOLS_PRICE_SPAN_CSS_SELECTOR

from modules.utils.selenium_utils import find_element_with_wait
from modules.utils.logger_loader import logger


class DexToolsParser(Singleton):
    def __init__(self):
        self.driver_service = DriverService(startup_page=DEX_COIN_URL, use_cookies=False)
        self.driver = self.driver_service.get_driver()

    def get_price(self) -> float | None:
        try:
            price_element = find_element_with_wait(self.driver, DEX_TOOLS_PRICE_SPAN_CSS_SELECTOR, By.CSS_SELECTOR)
            price_text = price_element.text.strip().replace('$', '').replace(',', '.')

            return float(price_text)
        except (NoSuchElementException, TimeoutException) as e:
            logger.error('Price element not found.')
            return None
