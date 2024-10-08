from modules.services.mexc_service import MexcService
from modules.structs.side import Side
import time
from modules.utils.driver_utils import save_cookies

mexc_service = MexcService()

input('')

save_cookies(mexc_service.driver.get_cookies())



try:
    # Тестуємо метод set_position_size
    mexc_service.set_position_size(1.5)

    # Тестуємо метод open_position для LONG
    mexc_service.open_position(Side.LONG)

    # Чекаємо деякий час, щоб позиція відкрилася
    time.sleep(5)

    has_orders = mexc_service.is_active_orders()
    print(f"Active orders exist: {has_orders}")

    enter_price = mexc_service.get_enter_price()
    print(f"Enter price: {enter_price}")
    time.sleep(5)

    tp_price = enter_price * 1.01
    mexc_service.set_tp_by_limit(tp_price)

    mexc_service.close_any_limit_orders()

    mexc_service.set_tp_by_limit(tp_price)

    mexc_service.close_any_limit_orders()

    time.sleep(5)
    mexc_service.close_active_order_by_market()

except Exception as e:
    print(f"An error occurred during testing: {e}")
finally:
    mexc_service.driver.quit()
