param(
    [ValidateSet('chrome', 'edge', 'firefox')][string]$Browser = 'chrome',
    [ValidateRange(1, 10000000)][int]$MaxPrice = 2000,
    [ValidateRange(0, 10)][int]$PauseSeconds = 1,
    [switch]$Headless,
    [switch]$UiOnly
)
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    # Reuse the already-installed environment in this user's original workspace.
    $pythonPath = Join-Path (Split-Path -Parent $PSScriptRoot) '.venv/Scripts/python.exe'
}
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install the framework first: py -3 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e ".[dev]"'
}
$settings = @{
    QA_BROWSER = $Browser
    QA_HEADLESS = $Headless.IsPresent.ToString().ToLowerInvariant()
    QA_AMAZON_MAX_PRICE = [string]$MaxPrice
    QA_DEMO_PAUSE = [string]$PauseSeconds
    QA_TIMEOUT = '30'
    QA_AMAZON_URL_FALLBACK = (-not $UiOnly.IsPresent).ToString().ToLowerInvariant()
}
$previous = @{}
Push-Location $PSScriptRoot
try {
    foreach ($name in $settings.Keys) {
        $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $settings[$name], 'Process')
    }
    & $pythonPath -m pytest examples/test_amazon_price.py --run-integration -s --html=reports/amazon.html --junitxml=reports/amazon.xml -p no:cacheprovider
    $testExitCode = $LASTEXITCODE
} finally {
    foreach ($name in $previous.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
    }
    Pop-Location
}
exit $testExitCode
