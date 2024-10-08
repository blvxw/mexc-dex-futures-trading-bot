import ccxt
from .logger_loader import logger


mexc_futures = ccxt.mexc({
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True
})


def parse_price_mexc_futures(symbol: str) -> float | None:
    try:
        ticker = mexc_futures.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        logger.error(f"Error while fetching Mexc Futures price: {e}")
        return None
