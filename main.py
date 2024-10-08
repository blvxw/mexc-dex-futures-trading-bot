from modules.trading_algorithm import TradingAlgorithm
from modules.services.mexc_service import MexcService


def main():
    TradingAlgorithm().start_trade()


if __name__ == '__main__':
    main()