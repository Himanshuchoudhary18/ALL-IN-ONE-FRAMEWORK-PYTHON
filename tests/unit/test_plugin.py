"""Verify report evidence and fixture teardown in an intentionally failing child run."""
import os
import subprocess
import sys
from pathlib import Path


def test_failure_evidence_and_cleanup(tmp_path):
    source = '\n'.join([  # noqa: FLY002 -- lines make the generated fixture source readable
        'import base64',
        'from pathlib import Path',
        'import pytest',
        'from qa_framework.config import Settings',
        'pytest_plugins = ["qa_framework.pytest_plugin"]',
        '@pytest.fixture',
        'def settings():',
        '    return Settings(reports_dir="evidence")',
        '@pytest.fixture',
        'def driver():',
        '    class Driver:',
        '        def get_screenshot_as_base64(self):',
        '            return base64.b64encode(b"test-image").decode()',
        '    yield Driver()',
        '    Path("cleaned.txt").write_text("closed")',
    ])
    (tmp_path / "conftest.py").write_text(source, encoding="utf-8")
    (tmp_path / "test_failure.py").write_text('def test_failure(driver, settings):\n    assert False\n', encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "python")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "--html=report.html", "--self-contained-html"],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 1, result.stdout + result.stderr
    assert (tmp_path / "cleaned.txt").exists()
    assert list((tmp_path / "evidence/screenshots").glob("*.png"))
    assert "data:image/png;base64" in (tmp_path / "report.html").read_text(encoding="utf-8")
