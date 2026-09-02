$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    py -m venv (Join-Path $Root '.venv')
    & $Python -m pip install -r (Join-Path $Root 'requirements.txt')
    & $Python -m playwright install chromium
}

& $Python (Join-Path $Root 'naver_cafe_researcher.py') @args
exit $LASTEXITCODE
