from collections import deque
from modules.structs.side import Side
from modules.utils.logger_loader import logger

from data.config import (
    MEXC_NAME_COIN,
    MAX_LOOKBACK_TIME_SECONDS,
    MIN_PRICE_CHANGE_DEX,
    MIN_POTENTIAL_PROFIT,
    GAP_FILL,
    LEVERAGE,
    POSITION_SIZE_DIAPASON,
    TP_CHANGE_THRESHOLD,
    LOOP_DELAY,
    DECIMALS,
    MAX_PROFIT_PERCENTAGE
)


def clear_deque_prices(price_history: deque, max_lookback_time_seconds: int, now_time: float) -> deque:
    while len(price_history) > 0:
        old_time = price_history[0][0]
        if now_time - old_time <= max_lookback_time_seconds:
            break
        price_history.popleft()

    return price_history


def get_max_price_change_percentage(price_history: deque) -> dict | None:
    if len(price_history) < 2:
        return None

    last_price = price_history[-1][1]

    info = {
        "max_diff_percentage": 0,
        "timestamp": None
    }

    for i in range(len(price_history) - 2, -1, -1):
        price = price_history[i][1]
        diff = abs(price - last_price) / price * 100

        if diff > info["max_diff_percentage"]:
            info["max_diff_percentage"] = diff
            info["timestamp"] = price_history[i][0]

    if info["max_diff_percentage"] == 0:
        return None

    return info


def get_corresponding_price_change_percentage(price_history: deque, target_time: float) -> float | None:
    if len(price_history) < 2:
        return None

    last_price = price_history[-1][1]

    for i in range(len(price_history) - 2, -1, -1):
        if price_history[i][0] == target_time:
            return abs(price_history[i][1] - last_price) / price_history[i][1] * 100

    # If target_time not found, return None
    return None


def calc_tp_limit(side: Side, dex_last_price: float, enter_price: float, gap_fill: float, decimals: int) -> float:
    price_difference = abs(dex_last_price - enter_price)

    gap = price_difference * gap_fill

    if side == Side.LONG:
        tp_price = enter_price + gap
    else:
        tp_price = enter_price - gap

    return round(tp_price, decimals)


def calc_percent_profit_with_leverage(side: Side, enter_price: float, tp_price: float, leverage: float) -> float:
    if side == Side.LONG:
        profit_percentage = ((tp_price - enter_price) / enter_price) * 100
    else:
        profit_percentage = ((enter_price - tp_price) / enter_price) * 100
    profit_percentage_with_leverage = profit_percentage * leverage
    return round(profit_percentage_with_leverage, 2)


def calc_slippage_percentage(enter_price: float, mexc_price: float) -> float:
    return ((mexc_price - enter_price) / enter_price) * 100


def calc_position_size(potential_profit_percentage: float) -> int:
    position_size = POSITION_SIZE_DIAPASON[0] + (
            (potential_profit_percentage / MAX_PROFIT_PERCENTAGE) * (
                POSITION_SIZE_DIAPASON[1] - POSITION_SIZE_DIAPASON[0])
    )

    return int(min(position_size, POSITION_SIZE_DIAPASON[1]))


def check_trade_condition(dex_prices: deque, mexc_prices: deque,
                          dex_last_price: float, mexc_last_price: float) -> dict | None:

    dex_price_change_info = get_max_price_change_percentage(dex_prices)

    if dex_price_change_info is None:
        return None

    if MIN_PRICE_CHANGE_DEX > dex_price_change_info["max_diff_percentage"]:
        logger.debug(f'Max price change on DEX {dex_price_change_info["max_diff_percentage"]}%'
                     f' is less than {MIN_PRICE_CHANGE_DEX}%, skipping.')
        return None

    mexc_price_change_percentage = get_corresponding_price_change_percentage(
        mexc_prices, dex_price_change_info["timestamp"])

    if mexc_price_change_percentage is None:
        logger.debug('No corresponding price change in MEXC, skipping.')
        return None

    if abs(mexc_price_change_percentage) >= abs(dex_price_change_info["max_diff_percentage"]):
        logger.debug(f'Price change on MEXC {mexc_price_change_percentage}% is greater than on DEX'
                     f'{dex_price_change_info["max_diff_percentage"]}%, skipping.')
        return None

    price_difference_percentage = (dex_last_price - mexc_last_price) / dex_last_price * 100
    potential_profit_percentage = abs(price_difference_percentage * LEVERAGE)

    logger.debug(f'Price difference between DEX and MEXC: {price_difference_percentage:.2f}%')

    if potential_profit_percentage < MIN_POTENTIAL_PROFIT:
        logger.debug('Price movement direction does not match, skipping.')
        return None

    side = Side.LONG if price_difference_percentage > 0 else Side.SHORT
    position_size = calc_position_size(potential_profit_percentage)

    return {
        "side": side,
        "position_size": position_size,
    }


