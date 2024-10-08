import time


def smart_sleep(start_time, delay):
    diff = time.time() - start_time

    if diff < delay:
        time.sleep(delay - diff)
