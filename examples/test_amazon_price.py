"""Visible Amazon demo: search Shoes, apply a maximum price, dismiss the filter panel."""
import os
import time
from pathlib import Path

import pytest
from qa_framework.data import write_json
from qa_framework.pages.amazon import AmazonSearchPage

pytestmark = [pytest.mark.integration, pytest.mark.web]


def test_amazon_shoes_under_2000(driver, settings):
    maximum = int(os.getenv("QA_AMAZON_MAX_PRICE", "2000"))
    pause = float(os.getenv("QA_DEMO_PAUSE", "1"))
    if not 0 <= pause <= 10:
        raise ValueError("QA_DEMO_PAUSE must be between 0 and 10 seconds")
    page = AmazonSearchPage(driver, "https://www.amazon.in", settings.timeout)
    driver.set_window_size(1100, 900)  # Narrow desktop layout exposes the collapsible Filters panel.
    screenshots = Path(settings.reports_dir) / "amazon-demo"

    def step(number, description):
        print(f"STEP {number}: {description}", flush=True)
        page.screenshot(screenshots / f"{number:02d}.png")
        if pause:
            time.sleep(pause)  # Presentation pacing only; element synchronization uses explicit waits.

    page.open()
    page.wait_for_search()
    step(1, "Opened Amazon India")
    page.search_for("Shoes")
    step(2, 'Clicked search field, typed "Shoes", clicked Go; search results loaded')
    page.open_filters()
    step(3, "Opened price filters")
    method = page.set_maximum_price(maximum, allow_url_fallback=os.getenv("QA_AMAZON_URL_FALLBACK", "true") == "true")
    page.wait_for_applied_price(maximum)
    step(4, f"Amazon applied maximum price INR {maximum} using {method}")
    closed = page.close_filters_if_open()
    step(5, "Closed filter panel" if closed else "Panel already closed or layout uses a permanent sidebar")
    page.wait_for_applied_price(maximum)
    write_json(screenshots / "result.json", {"maximum_price_inr": maximum,
               "filter_panel_closed_by_test": closed, "filter_method": method, "filtered_url": driver.current_url})
    print(f"PASS: Shoes search with maximum INR {maximum}; final URL: {driver.current_url}", flush=True)
