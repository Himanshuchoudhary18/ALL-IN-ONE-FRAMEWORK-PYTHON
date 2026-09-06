"""Real browser smoke test against a local file; no external application is visited."""
import pytest
from selenium.webdriver.common.by import By

pytestmark = [pytest.mark.integration, pytest.mark.web]


def test_local_form(page, tmp_path):
    file = tmp_path / "form.html"
    file.write_text('<html><head><title>Local QA</title></head><body><input id="name">'
                    '<button id="submit" onclick="document.getElementById(\'result\').textContent='
                    'document.getElementById(\'name\').value">Submit</button><p id="result"></p>'
                    '</body></html>', encoding="utf-8")
    page.driver.get(file.as_uri())
    page.fill((By.ID, "name"), "TPDDL QA")
    page.click((By.ID, "submit"))
    page.assert_text((By.ID, "result"), "TPDDL QA")
