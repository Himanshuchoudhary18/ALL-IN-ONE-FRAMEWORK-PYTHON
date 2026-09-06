"""Python ports of the surviving demo workflows. No embedded endpoints or credentials.

Run explicitly: pytest examples --run-integration. These are not TPDDL workflows.
"""
import os

import pytest
from qa_framework.config import required_env
from qa_framework.waits import poll_until
from qa_framework.web import BasePage
from selenium.webdriver.common.by import By

pytestmark = pytest.mark.integration


class AmazonPage(BasePage):
    search = (By.ID, "twotabsearchtextbox")
    submit = (By.ID, "nav-search-submit-button")

    def search_for(self, product):
        self.fill(self.search, product)
        self.click(self.submit)


@pytest.mark.web
def test_amazon_search(driver, settings):
    page = AmazonPage(driver, required_env("QA_AMAZON_URL"), settings.timeout)
    page.open()
    page.search_for("Shoes")
    page.visible((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
    # Cart locators in the old example were result-position IDs. Supply current locators explicitly.
    if os.getenv("QA_AMAZON_ADD_CART_CSS"):
        page.click((By.CSS_SELECTOR, os.environ["QA_AMAZON_ADD_CART_CSS"]))
        page.visible((By.CSS_SELECTOR, required_env("QA_AMAZON_CART_CONFIRMATION_CSS")))


@pytest.mark.api
def test_avatar_response(api):
    api.get(required_env("QA_AVATAR_URL"), expected_status=200).assert_value(
        "status", 200
    ).assert_value("message", "Request successful")


@pytest.mark.database
def test_latest_test_otp(mongo_db):
    consumer = required_env("QA_TEST_MOBILE")
    collection = mongo_db[required_env("QA_OTP_COLLECTION")]
    row = poll_until(lambda: collection.find_one({"mobile_no": consumer}, sort=[("created_on", -1)]))
    assert row.get("otp") is not None
