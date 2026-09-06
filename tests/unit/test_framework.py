import importlib.util
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from qa_framework.api import APIClient, json_path
from qa_framework.config import Settings, required_env
from qa_framework.data import read_csv, read_excel, read_json, write_excel, write_json
from qa_framework.database import SQLDatabase
from qa_framework.web import BasePage, create_driver
from sqlalchemy.exc import IntegrityError


@pytest.fixture(scope="module")
def server_url():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(404 if self.path == "/missing" else 200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": 200, "data": [{"id": 7}]}).encode())

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            self.send_response(201)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    worker.join()


def test_api_real_http_status_and_schema(server_url):
    with APIClient(server_url) as client:
        result = client.get("/", expected_status=200)
        result.assert_value("data.0.id", 7).assert_schema({"type": "object", "required": ["data"]})
        result.assert_latency(5000)
        assert len(client.timings) == 1
        with pytest.raises(AssertionError, match="HTTP 200, got 404"):
            client.get("/missing", expected_status=200)


def test_post_payload(server_url):
    with APIClient(server_url) as client:
        assert client.post("/", json={"id": 12}, expected_status=201).json() == {"id": 12}


def test_no_unsafe_retries():
    with APIClient(retries=3) as client:
        assert "POST" not in client.session.get_adapter("https://").max_retries.allowed_methods
        assert client.session.verify is True


def test_json_path_missing_fails():
    with pytest.raises(KeyError):
        json_path({}, "missing")


def test_config_precedence(tmp_path, monkeypatch):
    path = tmp_path / "settings.toml"
    path.write_text('[default]\ntimeout=10\n[environments.uat]\ntimeout=20\n', encoding="utf-8")
    monkeypatch.setenv("QA_TIMEOUT", "30")
    monkeypatch.setenv("QA_HEADLESS", "false")
    settings = Settings.load(path, "uat")
    assert settings.timeout == 30
    assert settings.headless is False
    assert settings.environment == "uat"


@pytest.mark.parametrize("name,value", [("QA_TIMEOUT", "0"), ("QA_HEADLESS", "maybe"), ("QA_BROWSER", "unknown")])
def test_invalid_config(tmp_path, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.load(tmp_path / "missing.toml")


def test_missing_secret(monkeypatch):
    monkeypatch.delenv("QA_TEST_SECRET", raising=False)
    with pytest.raises(ValueError, match="QA_TEST_SECRET"):
        required_env("QA_TEST_SECRET")


def test_sql_parameterization_and_rollback():
    with SQLDatabase("sqlite://") as db:
        db.execute("CREATE TABLE consumer (id INTEGER PRIMARY KEY, name TEXT)")
        value = "O'Brien'; DROP TABLE consumer;--"
        db.execute("INSERT INTO consumer VALUES (:id, :name)", {"id": 1, "name": value})
        assert db.query("SELECT name FROM consumer WHERE id=:id", {"id": 1}) == [{"name": value}]
        with pytest.raises(IntegrityError):
            db.execute("INSERT INTO consumer VALUES (1, 'duplicate')")
        assert len(db.query("SELECT * FROM consumer")) == 1


def test_data_round_trip(tmp_path):
    rows = [{"id": 1, "name": "Test Consumer"}]
    write_json(tmp_path / "data.json", rows)
    assert read_json(tmp_path / "data.json") == rows
    write_excel(tmp_path / "data.xlsx", rows)
    assert read_excel(tmp_path / "data.xlsx") == rows
    (tmp_path / "data.csv").write_text('id,name\n1,"Test, Consumer"\n', encoding="utf-8")
    assert read_csv(tmp_path / "data.csv")[0]["name"] == "Test, Consumer"


@pytest.mark.parametrize("browser", ["chrome", "edge", "firefox"])
def test_browser_options(monkeypatch, browser):
    driver = MagicMock()
    constructor = MagicMock(return_value=driver)
    monkeypatch.setattr(f"qa_framework.web.webdriver.{browser.capitalize()}", constructor)
    assert create_driver(Settings(browser=browser)) is driver
    driver.implicitly_wait.assert_called_once_with(0)
    options = constructor.call_args.kwargs["options"]
    assert any("headless" in arg for arg in options.arguments)
    assert "--ignore-certificate-errors" not in options.arguments


def test_browser_cleanup_if_setup_fails(monkeypatch):
    driver = MagicMock()
    driver.set_window_size.side_effect = RuntimeError("setup failed")
    monkeypatch.setattr("qa_framework.web.webdriver.Chrome", lambda **kwargs: driver)
    with pytest.raises(RuntimeError):
        create_driver(Settings())
    driver.quit.assert_called_once()


def test_upload_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        BasePage(MagicMock()).upload(("id", "file"), tmp_path / "absent.txt")


def test_polling_succeeds_and_times_out():
    from qa_framework.waits import poll_until
    values = iter([None, {"otp": "test-only"}])
    assert poll_until(lambda: next(values), interval=0.001)["otp"] == "test-only"
    with pytest.raises(TimeoutError):
        poll_until(lambda: None, timeout=0.002, interval=0.001)


@pytest.mark.skipif(importlib.util.find_spec("locust") is None, reason="Install performance extra")
def test_locust_local_smoke(server_url, tmp_path):
    script = Path(__file__).resolve().parents[2] / "performance/locustfile.py"
    result = subprocess.run([sys.executable, "-m", "locust", "-f", str(script), "--host", server_url,
                             "--headless", "-u", "1", "-r", "1", "-t", "2s", "--csv", str(tmp_path / "load")],
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    statistics = read_csv(tmp_path / "load_stats.csv")
    total = next(row for row in statistics if row["Name"] == "Aggregated")
    assert int(total["Request Count"]) > 0
    assert int(total["Failure Count"]) == 0
