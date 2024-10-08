import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from modules.utils.logger_loader import logger


def find_element_with_wait(driver, query, method=By.XPATH,timeout=3):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((method, query))
        )
    except TimeoutException as e:
        logger.error(f"Елемент з XPath '{query}' не знайдено протягом {timeout} секунд.")
        raise e


def extract_order_count(text):
    match = re.search(r'\((\d+)\)', text)
    return int(match.group(1)) if match else 0
