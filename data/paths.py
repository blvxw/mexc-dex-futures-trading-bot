import pathlib

WORKING_DIR = pathlib.Path(__file__).parent.parent

# >>> LOGGING
LOGS_FOLDER_PATH = pathlib.Path(WORKING_DIR, 'logs')
LOGS_PATH = pathlib.Path(LOGS_FOLDER_PATH, 'logs')
SCREENSHOTS_FOLDER_PATH = pathlib.Path(LOGS_PATH, 'screenshots')
LOGGING_FILE_PATH = pathlib.Path(LOGS_FOLDER_PATH, 'log.txt')

# >>> COOKIES
COOKIES_FILE_PATH = pathlib.Path(WORKING_DIR, 'cookies.txt')
