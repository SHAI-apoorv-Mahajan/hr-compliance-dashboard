# PostToolUse hook on Edit|Write (Windows / PowerShell variant).
# Always exits 0 — formatting failures never block.

$ErrorActionPreference = "SilentlyContinue"
$input = [Console]::In.ReadToEnd()

try {
    $data = $input | ConvertFrom-Json
    $target = $data.tool_input.file_path
} catch {
    exit 0
}

if ([string]::IsNullOrEmpty($target) -or -not (Test-Path $target)) { exit 0 }

$ext = [System.IO.Path]::GetExtension($target).ToLower()

switch ($ext) {
    ".py" {
        if (Get-Command black -ErrorAction SilentlyContinue) {
            & black --quiet $target 2>$null
        }
    }
    { @(".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".md") -contains $_ } {
        if (Get-Command npx -ErrorAction SilentlyContinue) {
            & npx --no-install prettier --write --loglevel silent $target 2>$null
        }
    }
}

exit 0
