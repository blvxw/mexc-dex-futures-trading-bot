from collections import deque
from modules.structs.side import Side


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
    gap = abs(dex_last_price - enter_price) * gap_fill
    if side == Side.LONG:
        tp_price = dex_last_price + gap
    else:
        tp_price = dex_last_price - gap
    return round(tp_price, decimals)


def calc_percent_profit_with_leverage(side: Side, enter_price: float, tp_price: float, leverage: float) -> float:
    if side == Side.LONG:
        profit_percentage = ((tp_price - enter_price) / enter_price) * 100
    else:
        profit_percentage = ((enter_price - tp_price) / enter_price) * 100
    profit_percentage_with_leverage = profit_percentage * leverage
    return round(profit_percentage_with_leverage, 2)
