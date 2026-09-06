"""TOML configuration with QA_* environment overrides; secrets stay outside source."""
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    base_url: str = ""
    api_url: str = ""
    browser: str = "chrome"
    headless: bool = True
    timeout: float = 15
    page_load_timeout: float = 60
    remote_url: str = ""
    ca_bundle: str = ""
    reports_dir: str = "reports"

    @classmethod
    def load(cls, path="config/settings.toml", environment=None):
        document = tomllib.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}
        env = environment or os.getenv("QA_ENVIRONMENT", "local")
        values = dict(document.get("default", {}))
        values.update(document.get("environments", {}).get(env, {}))
        values["environment"] = env
        for name in cls.__dataclass_fields__:
            if name != "environment" and f"QA_{name.upper()}" in os.environ:
                values[name] = os.environ[f"QA_{name.upper()}"]
        if isinstance(values.get("headless"), str):
            if values["headless"].lower() not in {"true", "false"}:
                raise ValueError("QA_HEADLESS must be true or false")
            values["headless"] = values["headless"].lower() == "true"
        for name in ("timeout", "page_load_timeout"):
            if name in values:
                values[name] = float(values[name])
                if values[name] <= 0:
                    raise ValueError(f"{name} must be positive")
        settings = cls(**values)
        if settings.browser not in {"chrome", "firefox", "edge"}:
            raise ValueError("browser must be chrome, firefox or edge")
        return settings


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Set {name} before using this integration")
    return value
