[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$clientScript = Join-Path $skillDir "caido-client.ts"

if (-not (Test-Path -LiteralPath $clientScript)) {
  throw "Caido client not found at '$clientScript'."
}

& npx tsx $clientScript @RemainingArgs
exit $LASTEXITCODE
