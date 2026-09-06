"""TPDDL connection smoke checks. Replace/add business workflows after configuration."""
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.smoke]


@pytest.mark.web
def test_application_opens(page, settings):
    assert settings.base_url, "Set QA_BASE_URL"
    page.open()
    assert page.driver.title.strip(), "Application returned an empty page title"


@pytest.mark.api
def test_api_health(api, settings):
    import os
    assert settings.api_url, "Set QA_API_URL"
    api.get(os.getenv("QA_HEALTH_PATH", "/health"), expected_status=200)
