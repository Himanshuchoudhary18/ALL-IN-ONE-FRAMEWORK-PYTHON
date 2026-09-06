# Amazon India automation demo

This example searches **Shoes** and sets a **maximum price of INR 2,000**.
It does not mean products priced exactly INR 2,000.

## Run it

Open PowerShell in `PYTHON-QA-CLEAN` and run:

```powershell
.\run-amazon.ps1
```

The script uses Chrome in a visible window, with one-second pauses for presentation.
It uses this folder's virtual environment, or the existing environment one directory
above on this workstation. On a fresh clone, install first:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Alternative browser and presentation speed:

```powershell
.\run-amazon.ps1 -Browser edge -PauseSeconds 2
.\run-amazon.ps1 -Browser firefox -Headless
```

Install the selected browser. Chrome is the browser used for development verification;
support for Edge/Firefox does not mean this Amazon scenario has been verified on them.

## What the test does

1. Opens `https://www.amazon.in/`. Handles the observed ordinary **Continue shopping**
   landing button if present.
2. Clicks inside the search field, types `Shoes`, and clicks the search submit button.
   Clicking the submit button before typing is unnecessary.
3. Waits for product results, then opens **Filters** if the price controls are not already visible.
4. Reads the current price slider's mapping and selects exactly INR 2,000.
   Slider positions are indexes, not prices. The test changes the actual slider control
   and sends its normal input/change events; Amazon applies the filter automatically.
5. Checks the resulting URL to confirm the maximum is INR 2,000. Amazon may express
   it as `high-price=2000` or `p_36:-200000` (paise).
6. Closes the Filters panel if its Close button remains visible. Some layouts have a
   permanent sidebar or close automatically, so there may be no popup to dismiss.
7. Saves screenshots and a result summary, then closes the browser through fixture teardown.

Amazon changes available slider increments by search/session. If exactly INR 2,000
is unavailable, the demo uses the approved `high-price=2000` URL fallback. It prints
`FALLBACK` and records `filter_method` in result.json. This verifies the exact price
result, but that run does not demonstrate selecting INR 2,000 through the slider.
Use `.\run-amazon.ps1 -UiOnly` to disable fallback and fail if the exact slider value is unavailable.
CAPTCHA or other unsupported challenge pages also prevent successful completion; the
script does not solve them. A failure report is useful evidence of where execution stopped.

## Read the result

- `reports/amazon.html`: HTML pass/fail report with failure screenshot.
- `reports/amazon.xml`: machine-readable result.
- `reports/amazon-demo/01.png` through `05.png`: completed demo steps.
- `reports/amazon-demo/result.json`: final filter URL and popup-close status on success.

Development verification: the visible Chrome run completed the search and applied
`high-price=2000` through the slider on September 6, 2026. The filter panel was already
closed after application. Another observed session did not offer that slider value,
which is why the explicit fallback option is included.

Console `STEP` messages show completed steps. Only pytest's final result/exit code
establishes pass or fail; screenshots alone do not. This verifies the applied filter,
not every advertised product's price (variants and sponsored results may differ).

## Understand the code

- `examples/test_amazon_price.py`: readable business steps and evidence capture.
- `python/qa_framework/pages/amazon.py`: Amazon locators and page actions.
- `python/qa_framework/pytest_plugin.py`: creates the browser and closes it on success/failure.
- `tests/unit/test_amazon_price.py`: checks price mapping and filter verification without contacting Amazon.

To change the requested ceiling, use `-MaxPrice 3000`. To build another site flow,
create its page object with its own locators, then write a test calling those actions
and asserting the expected result after each important operation.
