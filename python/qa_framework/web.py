"""Browser lifecycle and reusable page-object actions."""
from pathlib import Path

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def create_driver(settings):
    options = {"chrome": webdriver.ChromeOptions, "edge": webdriver.EdgeOptions,
               "firefox": webdriver.FirefoxOptions}[settings.browser]()
    if settings.headless:
        options.add_argument("-headless" if settings.browser == "firefox" else "--headless=new")
    if settings.remote_url:
        driver = webdriver.Remote(command_executor=settings.remote_url, options=options)
    else:
        driver = {"chrome": webdriver.Chrome, "edge": webdriver.Edge,
                  "firefox": webdriver.Firefox}[settings.browser](options=options)
    try:
        driver.set_window_size(1920, 1080)
        driver.set_page_load_timeout(settings.page_load_timeout)
        driver.implicitly_wait(0)
        return driver
    except BaseException:
        driver.quit()
        raise


class BasePage:
    def __init__(self, driver, base_url="", timeout=15):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, timeout)

    def open(self, path=""):
        self.driver.get(path if path.startswith(("http://", "https://")) else f"{self.base_url}/{path.lstrip('/')}")
        return self

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def fill(self, locator, value):
        element = self.visible(locator)
        element.clear()
        element.send_keys(str(value))

    def text(self, locator):
        return self.visible(locator).text

    def attribute(self, locator, name):
        return self.visible(locator).get_attribute(name)

    def assert_text(self, locator, expected):
        assert self.text(locator) == expected

    def assert_hidden(self, locator):
        self.wait.until(EC.invisibility_of_element_located(locator))

    def wait_text(self, locator, text):
        self.wait.until(EC.text_to_be_present_in_element(locator, text))

    def select(self, locator, text):
        Select(self.visible(locator)).select_by_visible_text(text)

    def hover(self, locator):
        ActionChains(self.driver).move_to_element(self.visible(locator)).perform()

    def scroll_to(self, locator):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", self.visible(locator))

    def press_enter(self, locator):
        self.visible(locator).send_keys(Keys.ENTER)

    def upload(self, locator, path):
        file = Path(path).resolve(strict=True)
        self.wait.until(EC.presence_of_element_located(locator)).send_keys(str(file))

    def screenshot(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not self.driver.save_screenshot(str(path)):
            raise OSError("Browser failed to save screenshot")
        return path

    def refresh(self):
        self.driver.refresh()
