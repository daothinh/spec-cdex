[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bashScript = Join-Path $scriptDir "k"

if (-not (Test-Path -LiteralPath $bashScript)) {
  throw "Kage shim not found at '$bashScript'."
}

$bash = Get-Command bash -ErrorAction SilentlyContinue
if (-not $bash) {
  throw "bash is required to run Kage on Windows. Install Git Bash or WSL and ensure 'bash' is on PATH."
}

function Convert-ToBashPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $resolved = (Resolve-Path -LiteralPath $Path).Path
  if ($resolved -match '^([A-Za-z]):\\(.*)$') {
    $drive = $matches[1].ToLowerInvariant()
    $rest = $matches[2] -replace '\\', '/'
    return "/$drive/$rest"
  }
  return ($resolved -replace '\\', '/')
}

$bashScriptPath = Convert-ToBashPath -Path $bashScript

& $bash.Source "-lc" 'script="$(cygpath -u "$1" 2>/dev/null || printf "%s" "$1")"; shift; exec "$script" "$@"' -- $bashScriptPath @RemainingArgs
exit $LASTEXITCODE
