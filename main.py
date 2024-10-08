import threading
import keyboard
import time
from modules.trading_algorithm.trading_algorithm import TradingAlgorithm

if __name__ == '__main__':
    trading_algorithm = TradingAlgorithm()
    trade_thread = threading.Thread(target=trading_algorithm.start_trade)
    trade_thread.start()

    try:
        while not trading_algorithm.close_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    trade_thread.join()
