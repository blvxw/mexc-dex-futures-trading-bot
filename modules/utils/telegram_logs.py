import requests
from data.config import TELEGRAM_CHAT_ID
from data.urls import TELEGRAM_API_URL
from modules.utils.logger_loader import logger
import time


def send_log_to_telegram(message: str):
    try:
        response = requests.post(TELEGRAM_API_URL, data={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'})
        if response.status_code != 200:
            logger.error(f"Failed to send log to Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send log to Telegram: {e}")


def send_position_info_message_to_telegram(side: Side, position_size: float, enter_price: float, tp_limit: float,
                                           dex_price: float, mexc_price: float, percentage_profit_with_leverage: float):
    message_text = f'''
⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
-----------------------------
📈 Side: <b>{side.name}</b>
💵 Enter price: <b>{enter_price}</b>
💰 Position size: <b>{position_size} USDT</b>

💹 Potential profit: <b>{percentage_profit_with_leverage}%</b>

💱 MEXC: <b>{mexc_price}</b>
💱 DEX: <b>{dex_price}</b>

🎯 Take Profit: <b>{tp_limit}</b>'''

    send_log_to_telegram(message_text)


def send_new_tp_limit_message_to_telegram(tp_limit: float, mexc_price: float, dex_price: float,
                                          percentage_profit_with_leverage: float):
    message_text = f'''
⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
-----------------------------
🎯 New Take Profit: <b>{tp_limit}</b>

💱 MEXC: <b>{mexc_price}</b>
💱 DEX: <b>{dex_price}</b>

💹 Potential profit: <b>{percentage_profit_with_leverage}%</b>'''

    send_log_to_telegram(message_text)


def send_position_closed_message_to_telegram(enter_price: float, mexc_price: float, dex_price: float):
    message_text = f'''
⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
-----------------------------
🔴 Position closed due to adverse price movement.

💵 Enter price: <b>{enter_price}</b>
💱 MEXC: <b>{mexc_price}</b>
💱 DEX: <b>{dex_price}</b>'''

    send_log_to_telegram(message_text)

