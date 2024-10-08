from selenium.webdriver.chrome.options import Options
from data.driver.driver_config import OPTIONS_ARGS
from data.paths import COOKIES_FILE_PATH
from modules.utils.logger_loader import logger
from selenium.webdriver import Chrome
import os
import json


def get_chrome_options() -> Options | None:
    options = Options()

    for arg in OPTIONS_ARGS:
        options.add_argument(arg)

    return options


def save_cookies(cookies: list[dict]) -> None:
    if not os.path.exists(COOKIES_FILE_PATH):
        os.makedirs(os.path.dirname(COOKIES_FILE_PATH), exist_ok=True)

    with open(COOKIES_FILE_PATH, 'w', encoding='UTF-8') as f:
        try:
            json.dump(cookies, f)
        except Exception as e:
            logger.error(f"Error while saving cookies: {e}")


def get_cookies() -> list[dict] | None:
    if not os.path.exists(COOKIES_FILE_PATH):
        logger.info("Cookies file not found")
        return None

    cookies = []

    with open(COOKIES_FILE_PATH, 'r', encoding='UTF-8') as f:
        cookies_str = f.read()
        try:
            cookies = json.loads(cookies_str) if cookies_str else []
        except Exception as e:
            logger.error(f"Error while loading cookies: {e}")
            return None

    return cookies


def add_cookies(driver) -> None:
    cookies = get_cookies()

    if cookies:
        for cookie in cookies:
            driver.add_cookie(cookie)
