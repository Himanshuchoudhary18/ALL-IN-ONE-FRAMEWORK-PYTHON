import os

import pytest

pytest.importorskip("pytest_bdd")
from pytest_bdd import given, scenarios, then, when

pytestmark = pytest.mark.integration
scenarios("features/api.feature")


@given("a configured API health endpoint")
def configured(settings):
    assert settings.api_url, "Set QA_API_URL"


@when("I request the health endpoint", target_fixture="response")
def request_health(api):
    return api.get(os.getenv("QA_HEALTH_PATH", "/health"))


@then("the HTTP status is 200")
def assert_health(response):
    response.assert_status(200)
