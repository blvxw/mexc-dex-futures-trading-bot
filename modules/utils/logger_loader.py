import logging
import coloredlogs
from data.paths import LOGGING_FILE_PATH

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(LOGGING_FILE_PATH)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s %(levelname)s: %(message)s')
