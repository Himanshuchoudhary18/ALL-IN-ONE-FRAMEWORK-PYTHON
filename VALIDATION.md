# Validation record

The source framework was validated locally on Windows with Python 3.12.14 before this export.
Generated reports, the installed environment and the built wheel are not included in the clean copy.

- Default suite: 19 passed, 3 opt-in checks skipped; two pytest-xdist workers.
- Real Chrome local-form test: 1 passed separately outside the execution sandbox.
- Localhost Locust smoke: requests completed with no failures (part of default suite when performance extra is installed).
- Intentional child-test failure: nonzero exit, screenshot embedding and fixture cleanup verified.
- Ruff: Python framework, tests, load scenario and examples checked.
- pip check: no broken requirements.
- Wheel: built successfully; contains Python framework and package metadata only.
- Four external demo/BDD examples collect successfully without contacting their services.

Reports are generated under `reports/`; `report.html` covers default tests and
`browser.html` covers the separate real Chrome test. Exact installed package versions
are recorded in `requirements-lock-windows-py312.txt`.

TPDDL application checks, remote databases, SSH, mobile devices and hosted CI have
not been exercised against live environments. Database self-tests use SQLite; browser
unit tests use mocks in addition to the separate real Chrome check. The optional
integrations are implementations awaiting environment validation, not certified company coverage.

The first sandboxed Chrome launch failed; an unsandboxed retry with a fresh pytest
temporary directory passed. On this host, mixing sandboxed/unsandboxed pytest runs
can cause Windows temporary-directory ownership conflicts. Use a fresh `--basetemp`
and `-p no:cacheprovider` if reproducing the separate browser test across those contexts.
