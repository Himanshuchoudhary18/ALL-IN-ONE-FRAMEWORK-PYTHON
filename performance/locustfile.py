"""Run only against an explicitly supplied test host; no production defaults."""
import os

from locust import HttpUser, between, task


class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health(self):
        path = os.getenv("QA_LOAD_PATH", "/health")
        expected = int(os.getenv("QA_LOAD_STATUS", "200"))
        with self.client.get(path, name="configured endpoint", catch_response=True, timeout=15) as response:
            if response.status_code != expected:
                response.failure(f"Expected HTTP {expected}, received {response.status_code}")
