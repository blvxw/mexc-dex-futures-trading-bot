#
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


# >>> UTILS
from modules.utils.logger_loader import logger
from modules.utils.driver_utils import add_cookies, save_cookies, get_chrome_options

# >>> MISC
import time
import os


class DriverService:
    def __init__(self, startup_page: str, use_cookies: bool = False):
        self.use_cookies = use_cookies

        self.driver = Chrome(options=get_chrome_options())

        self.driver.maximize_window()
        self.driver.get(startup_page)

        if use_cookies:
            add_cookies(self.driver)
            self.driver.refresh()

        time.sleep(5)

    def get_driver(self):
        return self.driver

    def save_cookies(self):
        if self.use_cookies:
            save_cookies(self.driver.get_cookies())

    def close_driver(self):
        try:
            if self.use_cookies:
                save_cookies(self.driver.get_cookies())

            self.driver.quit()
            logger.info('Driver closed')
        except Exception as e:
            logger.error(f"Error while closing driver: {e}")
            exit(1)
