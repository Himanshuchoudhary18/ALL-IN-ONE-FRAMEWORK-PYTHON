"""HTTP sessions, real HTTP status checks, schema checks and latency measurements."""
import csv
import io
import logging
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests
from jsonschema import validate
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def json_path(value, path):
    """Resolve dotted dictionary keys and numeric list indexes (e.g. data.0.id)."""
    for part in path.split(".") if path else []:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


@dataclass
class APIResponse:
    raw: requests.Response

    @property
    def elapsed_ms(self):
        return self.raw.elapsed.total_seconds() * 1000

    def json(self):
        return self.raw.json()

    def csv(self):
        return list(csv.DictReader(io.StringIO(self.raw.text)))

    def assert_status(self, expected):
        assert self.raw.status_code == expected, f"Expected HTTP {expected}, got {self.raw.status_code}"
        return self

    def assert_schema(self, schema):
        validate(self.json(), schema)
        return self

    def assert_value(self, path, expected):
        actual = json_path(self.json(), path)
        assert actual == expected, f"Response field {path} does not match expected value"
        return self

    def assert_latency(self, maximum_ms):
        assert self.elapsed_ms <= maximum_ms, f"Response exceeded {maximum_ms} ms"
        return self

    def as_model(self, model):
        payload = self.json()
        return model.model_validate(payload) if hasattr(model, "model_validate") else model(**payload)


class APIClient:
    def __init__(self, base_url="", timeout=15, ca_bundle="", retries=0, headers=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = ca_bundle or True
        self.session.headers.update(headers or {})
        # Never automatically replay mutating requests.
        retry = Retry(total=retries, backoff_factor=0.5, allowed_methods={"GET", "HEAD", "OPTIONS"},
                      status_forcelist=[429, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.timings = []

    def request(self, method, path="", expected_status=None, **kwargs):
        url = path if path.startswith(("http://", "https://")) else f"{self.base_url}/{path.lstrip('/')}"
        if urlsplit(url).scheme not in {"http", "https"}:
            raise ValueError("Supply an HTTP(S) base URL or absolute request URL")
        response = APIResponse(self.session.request(method, url, timeout=kwargs.pop("timeout", self.timeout), **kwargs))
        # Deliberately omit URL, payload, cookies and headers: these may contain credentials or consumer data.
        self.timings.append({"method": method.upper(), "status": response.raw.status_code,
                             "elapsed_ms": response.elapsed_ms})
        logger.info("HTTP %s status=%s duration_ms=%.1f", method.upper(), response.raw.status_code, response.elapsed_ms)
        if expected_status is not None:
            response.assert_status(expected_status)
        return response

    def get(self, path="", **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path="", **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path="", **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path="", **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path="", **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
