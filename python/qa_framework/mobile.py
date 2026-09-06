"""Optional Appium client; an independently configured Appium server is required."""
from contextlib import contextmanager


@contextmanager
def mobile_driver(server_url, capabilities):
    from appium import webdriver
    from appium.options.common import AppiumOptions
    driver = webdriver.Remote(server_url, options=AppiumOptions().load_capabilities(capabilities))
    try:
        yield driver
    finally:
        driver.quit()
