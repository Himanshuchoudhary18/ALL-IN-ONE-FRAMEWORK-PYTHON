"""Explicit pytest plugin: settings, per-test resources and failure evidence."""
import logging
import os
from pathlib import Path
from uuid import uuid4

import pytest

from qa_framework.api import APIClient
from qa_framework.config import Settings, required_env
from qa_framework.database import SQLDatabase, firestore_client, mongo_database, redis_client
from qa_framework.web import BasePage, create_driver


def pytest_addoption(parser):
    group = parser.getgroup("qa")
    group.addoption("--qa-config", default="config/settings.toml")
    group.addoption("--env", default=None)
    group.addoption("--run-integration", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="External test: enable with --run-integration"))


@pytest.fixture(scope="session")
def settings(pytestconfig):
    return Settings.load(pytestconfig.getoption("--qa-config"), pytestconfig.getoption("--env"))


@pytest.fixture
def api(settings):
    with APIClient(settings.api_url, settings.timeout, settings.ca_bundle) as client:
        yield client


@pytest.fixture
def driver(settings):
    browser = create_driver(settings)
    try:
        yield browser
    finally:
        browser.quit()


@pytest.fixture
def page(driver, settings):
    return BasePage(driver, settings.base_url, settings.timeout)


@pytest.fixture
def sql_db():
    with SQLDatabase(required_env("QA_SQL_URL")) as db:
        yield db


@pytest.fixture
def mongo_db():
    with mongo_database(required_env("QA_MONGO_URI"), required_env("QA_MONGO_DATABASE")) as db:
        yield db


@pytest.fixture
def redis_db():
    with redis_client(required_env("QA_REDIS_URL")) as client:
        yield client


@pytest.fixture
def firestore_db():
    with firestore_client(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) as client:
        yield client


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    browser = item.funcargs.get("driver")
    if report.failed and browser is not None and report.when in {"setup", "call"}:
        try:
            import pytest_html
            settings = item.funcargs.get("settings", Settings())
            directory = Path(settings.reports_dir) / "screenshots"
            directory.mkdir(parents=True, exist_ok=True)
            image = browser.get_screenshot_as_base64()
            import base64
            (directory / f"{uuid4().hex}.png").write_bytes(base64.b64decode(image))
            report.extras = [*getattr(report, "extras", []), pytest_html.extras.png(image)]
        except Exception:  # noqa: BLE001 -- evidence failure must not hide the original test failure
            logging.getLogger(__name__).warning("Could not capture browser failure screenshot")
