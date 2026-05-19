# PreToolUse hook on Write|Edit (Windows / PowerShell variant).
# Exit 2 = blocked. Exit 0 = allow.

$ErrorActionPreference = "Stop"
$input = [Console]::In.ReadToEnd()

try {
    $data = $input | ConvertFrom-Json
    $target = $data.tool_input.file_path
} catch {
    exit 0
}

if ([string]::IsNullOrEmpty($target)) { exit 0 }

$norm = $target -replace '\\', '/'

$blocked = @(
    '\.env$',
    '\.env\.[^/]+$',
    '/secrets/',
    '/credentials\.json$',
    '/credentials\.[^/]+\.json$'
)

foreach ($pattern in $blocked) {
    if ($norm -match $pattern) {
        [Console]::Error.WriteLine("block-secret-writes: refusing to write to $target")
        exit 2
    }
}

exit 0
