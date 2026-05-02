[CmdletBinding()]
param(
    [ValidateSet("status", "guide", "ensure")]
    [string]$Mode = "status"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$tools = @(
    @{
        Name = "slither"
        Label = "Slither"
        Install = "py -m pip install --user slither-analyzer"
        Blocks = @(
            "Solidity static extraction",
            "ERC conformance checks",
            "upgradeability review automation"
        )
    },
    @{
        Name = "forge"
        Label = "Foundry"
        Install = "Use https://book.getfoundry.sh/getting-started/installation"
        Blocks = @(
            "mainnet fork replay",
            "Foundry PoC validation",
            "state-diff simulation"
        )
    },
    @{
        Name = "echidna"
        Label = "Echidna"
        Install = "Download a release from https://github.com/crytic/echidna/releases"
        Blocks = @(
            "EVM invariant fuzzing"
        )
    },
    @{
        Name = "medusa"
        Label = "Medusa"
        Install = "go install github.com/crytic/medusa@latest"
        Blocks = @(
            "parallel smart-contract fuzzing"
        )
    },
    @{
        Name = "trailmark"
        Label = "Trailmark"
        Install = "uv pip install trailmark"
        Blocks = @(
            "graph-based attack-surface and blast-radius analysis"
        )
    }
)

$rows = foreach ($tool in $tools) {
    $cmd = Get-Command $tool.Name -ErrorAction SilentlyContinue
    [pscustomobject]@{
        Tool = $tool.Label
        Command = $tool.Name
        Status = if ($cmd) { "installed" } else { "missing" }
        Source = if ($cmd) { $cmd.Source } else { "" }
        Install = $tool.Install
        Blocks = ($tool.Blocks -join "; ")
    }
}

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @($py.Source, "-m", "pip")
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @($python.Source, "-m", "pip")
    }

    return @()
}

function Ensure-Tool {
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Tool
    )

    switch ($Tool.Name) {
        "slither" {
            $pip = Get-PythonCommand
            if (-not $pip) { return "skipped" }
            & $pip[0] $pip[1] $pip[2] install --user slither-analyzer
            return if ($LASTEXITCODE -eq 0) { "ok" } else { "error" }
        }
        "medusa" {
            $go = Get-Command go -ErrorAction SilentlyContinue
            if (-not $go) { return "skipped" }
            & $go.Source install github.com/crytic/medusa@latest
            return if ($LASTEXITCODE -eq 0) { "ok" } else { "error" }
        }
        "trailmark" {
            $pip = Get-PythonCommand
            if (-not $pip) { return "skipped" }
            & $pip[0] $pip[1] $pip[2] install --user trailmark
            return if ($LASTEXITCODE -eq 0) { "ok" } else { "error" }
        }
        default {
            return "skipped"
        }
    }
}

if ($Mode -eq "ensure") {
    foreach ($tool in $tools) {
        $cmd = Get-Command $tool.Name -ErrorAction SilentlyContinue
        if ($cmd) {
            Write-Host "[web3-bootstrap] $($tool.Label) already installed"
            continue
        }

        $result = Ensure-Tool -Tool ([pscustomobject]$tool)
        Write-Host "[web3-bootstrap] $($tool.Label) auto-install result: $result"
    }
}

if ($Mode -eq "guide") {
    $rows |
        Select-Object Tool, Command, Install, Blocks |
        Format-Table -Wrap -AutoSize
    exit 0
}

$rows |
    Select-Object Tool, Command, Status, Source |
    Format-Table -Wrap -AutoSize

$missing = $rows | Where-Object { $_.Status -eq "missing" }
if ($missing) {
    Write-Host ""
    Write-Host "Missing tool guidance:" -ForegroundColor Yellow
    $missing |
        Select-Object Tool, Install, Blocks |
        Format-Table -Wrap -AutoSize
}
