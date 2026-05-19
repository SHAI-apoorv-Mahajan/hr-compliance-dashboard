# Stop hook (Windows / PowerShell variant).
# Exit 2 if any suite fails. Exit 0 if green or no tests yet.

$ErrorActionPreference = "Continue"
$failed = $false

if ((Test-Path "backend") -and (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Push-Location backend
    try {
        & pytest -q --no-header
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    } finally {
        Pop-Location
    }
}

if ((Test-Path "frontend") -and (Test-Path "frontend/package.json")) {
    $pkg = Get-Content "frontend/package.json" -Raw
    if ($pkg -match '"test"\s*:') {
        Push-Location frontend
        try {
            & npm test --silent
            if ($LASTEXITCODE -ne 0) { $failed = $true }
        } finally {
            Pop-Location
        }
    }
}

if ($failed) {
    [Console]::Error.WriteLine("run-tests-on-stop: test suite failed")
    exit 2
}

exit 0
