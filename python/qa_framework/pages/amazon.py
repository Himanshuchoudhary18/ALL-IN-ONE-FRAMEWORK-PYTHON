"""Amazon India search and price filtering, using the site's rendered controls."""
import json
from decimal import Decimal
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from qa_framework.web import BasePage


def slider_index(properties, rupees):
    """Slider indexes are not rupee values; read Amazon's current mapping."""
    target = Decimal(str(rupees))
    if target <= 0:
        raise ValueError("Maximum price must be positive")
    for index, value in enumerate(properties["stepValues"]):
        if value is not None and Decimal(str(value)) == target:
            return index
    raise ValueError(f"Amazon's current slider does not offer exactly INR {rupees}; no rounded filter applied")


def has_maximum_price(url, rupees):
    query = parse_qs(urlsplit(url).query)
    direct = query.get("high-price", [])
    if direct:
        try:
            return Decimal(direct[0]) == Decimal(str(rupees))
        except ArithmeticError:
            return False
    for refinement in ",".join(query.get("rh", [])).split(","):
        if refinement.startswith("p_36:"):
            upper = refinement.removeprefix("p_36:").partition("-")[2]
            return upper == str(int(Decimal(str(rupees)) * 100))
    return False


def exact_price_url(url, rupees):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in {"amazon.in", "www.amazon.in"}:
        raise ValueError("Price fallback requires an Amazon India HTTPS URL")
    price = Decimal(str(rupees))
    if not price.is_finite() or price <= 0:
        raise ValueError("Maximum price must be positive and finite")
    query = parse_qs(parts.query)
    refinements = [item for item in ",".join(query.pop("rh", [])).split(",")
                   if item and not item.startswith("p_36:")]
    if refinements:
        query["rh"] = [",".join(refinements)]
    query.pop("low-price", None)
    query["high-price"] = [str(price)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), ""))


class AmazonSearchPage(BasePage):
    SEARCH = (By.ID, "twotabsearchtextbox")
    SEARCH_BUTTON = (By.ID, "nav-search-submit-button")
    RESULTS = (By.CSS_SELECTOR, "[data-component-type='s-search-result']")
    FILTER_BUTTON = (By.ID, "s-all-filters-announce")
    PRICE_FORM = (By.CSS_SELECTOR, "#priceRefinements form[data-slider-props]")
    MAXIMUM = (By.CSS_SELECTOR, "input[aria-label='Maximum price']")
    CLOSE_FILTERS = (By.CSS_SELECTOR, "#s-refinements-header button[aria-label='Close']")

    def wait_for_search(self):
        continue_button = (By.XPATH, "//button[normalize-space()='Continue shopping']")
        self.wait.until(lambda _: self._displayed(self.SEARCH) or self._displayed(continue_button),
                        message="Amazon search unavailable; inspect the screenshot for a challenge or changed layout")
        if not self._displayed(self.SEARCH):
            self.click(continue_button)
        self.visible(self.SEARCH)

    def search_for(self, product):
        self.click(self.SEARCH)
        self.fill(self.SEARCH, product)
        self.click(self.SEARCH_BUTTON)
        self.visible(self.RESULTS)
        assert self.attribute(self.SEARCH, "value").casefold() == product.casefold()

    def _displayed(self, locator):
        try:
            return next((el for el in self.driver.find_elements(*locator) if el.is_displayed()), None)
        except StaleElementReferenceException:
            return None

    def open_filters(self):
        # Desktop layouts may already have a permanently visible sidebar.
        if not self._displayed(self.MAXIMUM):
            self.click(self.FILTER_BUTTON)
        self.visible(self.MAXIMUM)
        self.scroll_to(self.MAXIMUM)

    def set_maximum_price(self, rupees, allow_url_fallback=False):
        form = self.visible(self.PRICE_FORM)
        properties = json.loads(form.get_attribute("data-slider-props"))
        try:
            index = slider_index(properties, rupees)
        except ValueError:
            if not allow_url_fallback:
                raise
            print(f"FALLBACK: slider does not offer INR {rupees}; applying the exact price URL parameter", flush=True)
            self.driver.get(exact_price_url(self.driver.current_url, rupees))
            return "exact-price-url-fallback"
        slider = self.visible(self.MAXIMUM)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", slider)
        # Change the actual UI control and fire its normal events. No URL shortcut,
        # hidden field edits, or direct service calls: Amazon applies the filter itself.
        self.driver.execute_script(
            "const slider = arguments[0]; slider.value = String(arguments[1]);"
            "slider.dispatchEvent(new Event('input', {bubbles: true}));"
            "slider.dispatchEvent(new Event('change', {bubbles: true}));", slider, index,
        )
        return "slider-input-events"

    def wait_for_applied_price(self, rupees):
        self.wait.until(lambda driver: has_maximum_price(driver.current_url, rupees),
                        message=f"Amazon did not apply the requested INR {rupees} maximum")
        self.visible(self.RESULTS)

    def close_filters_if_open(self):
        close = self._displayed(self.CLOSE_FILTERS)
        if close is None:
            return False
        close.click()
        self.wait.until(EC.invisibility_of_element_located(self.CLOSE_FILTERS))
        return True
