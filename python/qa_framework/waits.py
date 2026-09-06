"""Bounded polling for asynchronous application state, including test OTP records."""
import time


def poll_until(fetch, predicate=bool, timeout=15, interval=0.25):
    if timeout <= 0 or interval <= 0:
        raise ValueError("timeout and interval must be positive")
    deadline = time.monotonic() + timeout
    while True:
        value = fetch()
        if predicate(value):
            return value
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Condition was not satisfied before the polling deadline")
        time.sleep(min(interval, remaining))
