param(
    [ValidateSet("patch", "minor", "major")]
    [string]$VersionPart,
    [switch]$Commit,
    [switch]$Tag,
    [switch]$Push,
    [switch]$DryRun
)

$arguments = @()
if ($VersionPart) { $arguments += @("--version-part", $VersionPart) }
if ($Commit) { $arguments += "--commit" }
if ($Tag) { $arguments += "--tag" }
if ($Push) { $arguments += "--push" }
if ($DryRun) { $arguments += "--dry-run" }

$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

& $python -m projectfoundry.scripts.release @arguments
exit $LASTEXITCODE
