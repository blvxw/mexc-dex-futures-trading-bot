import pyautogui
from modules.utils.get_time import get_time, format_time

from data.paths import SCREENSHOTS_FOLDER_PATH


def make_screenshot_logs() -> str:
    screenshot = pyautogui.screenshot()

    time_info: dict = get_time()

    now = format_time(time_info['datetime'])
    abbreviation = time_info['abbreviation']

    screenshot.save(f"{SCREENSHOTS_FOLDER_PATH}/{now} {abbreviation}.png")

    return f"{SCREENSHOTS_FOLDER_PATH}/{now}_{abbreviation}.png"
