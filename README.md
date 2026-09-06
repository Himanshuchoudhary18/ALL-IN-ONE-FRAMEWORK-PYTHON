# Python QA All-in-One Framework

For the visible Shoes search and INR 2,000 price-filter example, see [AMAZON-DEMO.md](AMAZON-DEMO.md).
Run it from this folder with `.\run-amazon.ps1`.

Python 3.11+ framework for web, API, SQL/NoSQL, SSH, test data, reporting and performance automation.
Python execution requires no Maven or JDK. This clean export contains only the Python framework,
examples, configuration templates, CI definitions and documentation. Legacy Java files and Git history
are excluded.

## Quick start (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,database,performance,bdd,mobile]"
.\.venv\Scripts\python.exe -m pytest -n 2
```

Install `.[dev]` for core features only. On Linux/macOS use `python3 -m venv .venv` and
`.venv/bin/python`. Default tests use localhost HTTP, SQLite and mocked browser drivers.
Reports: `reports/report.html` and `reports/junit.xml`; browser failure screenshots are embedded
in HTML and saved separately. Create your own `.venv` using the installation commands above.

## Framework components

| Area | Python implementation |
| --- | --- |
| Runner | pytest fixtures, markers, parametrization, xdist workers, optional reruns |
| Web | Selenium Chrome/Edge/Firefox and Grid, page objects, waits, uploads, screenshots |
| API | Requests sessions, JSON/forms/files/auth, status/schema/field/latency checks, safe-method retries |
| SQL | SQLAlchemy bound parameters and transactions, SQLite/PostgreSQL/MySQL |
| NoSQL | MongoDB, Redis and Firestore context managers and fixtures |
| SSH | Paramiko verified-host local forwarding |
| Data | JSON, CSV, XLSX utilities and Faker for generated data |
| Reports | pytest-html with failure evidence, JUnit XML, captured Python logging |
| Performance | Configurable Locust HTTP scenario |
| Optional | pytest-bdd dependency and Appium client wrapper |
| CI | GitHub Actions and Jenkins definitions |

Code is in `python/qa_framework`, tests in `tests`, load scenarios in `performance`.
Only the Python package is included in a built wheel.

`examples/` contains opt-in Python Amazon search/cart, avatar API and MongoDB OTP examples,
plus a runnable BDD health feature. Run with `pytest examples --run-integration` after supplying
the variables requested by each example. These examples are outside default test discovery.
The local real-browser smoke check can be run with
`pytest tests/browser --run-integration`; it opens only a generated local HTML form.

`requirements-lock-windows-py312.txt` records the exact installed versions validated in this checkout.
Use it as a constraints file with `pip install -c requirements-lock-windows-py312.txt -e ".[dev,database,performance,bdd,mobile]"`
on Windows/Python 3.12. It includes Windows-specific packages; resolve dependencies separately on other platforms.

## TPDDL configuration

Set non-secret defaults in `config/settings.toml`. Precedence: default table, selected environment,
then `QA_*` environment variables. `--env` overrides `QA_ENVIRONMENT` for environment selection.
`.env.example` documents variables; `.env` files are not automatically loaded.

```powershell
$env:QA_BASE_URL = "https://your-uat-application.example"
$env:QA_API_URL = "https://your-uat-api.example"
$env:QA_HEALTH_PATH = "/health"
.\.venv\Scripts\python.exe -m pytest tests/integration --env uat --run-integration
```

External tests are skipped unless explicitly enabled. Supplied connection checks are starter checks,
not validated TPDDL business workflows. Replace locators, endpoints, authentication and assertions
with your application requirements. Browsers must be installed for web tests; Selenium Manager may
need network access to resolve drivers. `QA_REMOTE_URL` selects an existing Grid.

Use external environment/CI secrets, and `QA_CA_BUNDLE` for corporate TLS certificates. TLS and SSH
host verification are enabled. Company database/SSH settings and Firebase account values have been
cleared from the working source files. Earlier Git commits can still contain the original credentials;
clearing current files does not remove those historical copies. Their owners should replace/rotate
exposed credentials. Screenshots and logs from your own tests may contain company data.

## Writing tests

`tests/conftest.py` loads `qa_framework.pytest_plugin`. Use the same `pytest_plugins` declaration
in another test project's root conftest.py after installing the package.

```python
import pytest
from selenium.webdriver.common.by import By
from qa_framework.web import BasePage

class LoginPage(BasePage):
    username = (By.ID, "username")  # replace with real locators
    password = (By.ID, "password")
    submit = (By.CSS_SELECTOR, "button[type=submit]")

    def login(self, username, password):
        self.fill(self.username, username)
        self.fill(self.password, password)
        self.click(self.submit)

@pytest.mark.integration
@pytest.mark.api
def test_consumers(api):
    api.get("/consumers", expected_status=200).assert_schema({"type": "array"})
```

Fixtures: `settings`, `api`, `driver`, `page`, `sql_db`, `mongo_db`, `redis_db`, `firestore_db`.
Browser and database resources close on failure. API supports `params`, `json`, `data`, `files`,
`auth`, `allow_redirects` and per-call `timeout`. Use `api.session.auth` for basic auth or update
session headers with a bearer token. Close opened upload files yourself. `APIResponse` provides
`.json()`, `.csv()`, `.as_model(Model)`, `.assert_schema()`, `.assert_value()` and `.assert_latency()`.
Dotted paths such as `data.0.id` are supported, not full JSONPath. Latency is response-header elapsed
time rather than full download time. Built-in HTTP metadata logs omit URLs, headers and bodies.

```python
def test_database(sql_db):
    rows = sql_db.query("SELECT id FROM consumers WHERE id=:id", {"id": 123})
    assert len(rows) == 1
```

`QA_SQL_URL` accepts `postgresql+psycopg://...`, `mysql+pymysql://...` or `sqlite://`.
SQL writes commit per `execute` call. Keep data-changing tests in test environments. Other database
variables are documented in `.env.example`. SSH forwarding returns a local host/port:

```python
from qa_framework.ssh import ssh_tunnel

with ssh_tunnel("bastion.example", "qa", "db.internal", 5432,
                key_filename="/secure/id_ed25519", known_hosts="/secure/known_hosts") as (host, port):
    pass  # connect a database client to host/port inside this block
```

## Selection, retries and performance

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke --run-integration
.\.venv\Scripts\python.exe -m pytest --reruns 1 --reruns-delay 2
.\.venv\Scripts\python.exe -m locust -f performance/locustfile.py --host http://localhost:8000 --headless -u 2 -r 1 -t 10s --csv reports/load
```

Retries default to off. Prefer independent tests and fixture setup over ordered dependencies.
Locust requires an explicit host. Configure `QA_LOAD_PATH` and `QA_LOAD_STATUS`; extend the task
with actual journeys and thresholds. Deleted Gatling journeys are not recreated or claimed to have
identical metrics. Optional BDD: install `.[bdd]` and bind Gherkin steps with pytest-bdd. Optional
mobile: install `.[mobile]` and use `mobile_driver(server_url, capabilities)` from
`qa_framework.mobile`; Appium server, platform drivers and devices are separate prerequisites.

## Validation and migration boundaries

```powershell
.\.venv\Scripts\python.exe -m ruff check python tests performance
.\.venv\Scripts\python.exe -m pytest -n 2
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m build --wheel
```

The framework replaces the Java lifecycle, web/API/database infrastructure, reports, data utilities
and load entry point. Application-specific fare/OTP logic and Amazon/Coca-Cola journeys are legacy
examples rather than TPDDL workflows. XLSX is supported; binary XLS is not. External database, SSH,
mobile, CI and company endpoints need environment validation. Python self-tests cover local HTTP,
SQLite, configuration, data round trips, browser setup mocks and report/cleanup hooks.
