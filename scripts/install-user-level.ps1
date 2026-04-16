[CmdletBinding()]
param(
    [ValidateSet("install", "status", "uninstall")]
    [string]$Mode = "install",

    [string]$CodexHome = (Join-Path $HOME ".codex"),

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$marketplacePath = Join-Path $repoRoot ".agents\plugins\marketplace.json"

function Normalize-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Get-LinkEntries {
    $catalog = Get-Content -Raw $marketplacePath | ConvertFrom-Json
    $entries = @(
        [pscustomobject]@{
            Name = "catalog-dir"
            LinkPath = (Normalize-Path (Join-Path $CodexHome ".agents\plugins"))
            TargetPath = (Normalize-Path (Join-Path $repoRoot ".agents\plugins"))
        }
    )

    foreach ($plugin in $catalog.plugins) {
        $sourcePath = $plugin.source.path -replace "^[.][/\\]", ""
        $pluginDir = Split-Path $sourcePath -Leaf
        $entries += [pscustomobject]@{
            Name = "plugin:$($plugin.name)"
            LinkPath = (Normalize-Path (Join-Path $CodexHome "plugins\$pluginDir"))
            TargetPath = (Normalize-Path (Join-Path $repoRoot $sourcePath))
        }
    }

    return $entries
}

function Get-LinkState {
    param([Parameter(Mandatory = $true)]$Entry)

    if (-not (Test-Path -LiteralPath $Entry.LinkPath)) {
        return [pscustomobject]@{
            Name = $Entry.Name
            LinkPath = $Entry.LinkPath
            TargetPath = $Entry.TargetPath
            State = "missing"
            CurrentTarget = $null
        }
    }

    $item = Get-Item -LiteralPath $Entry.LinkPath -Force
    $currentTarget = $null
    $linkType = ""

    if ($item.PSObject.Properties.Name -contains "LinkType") {
        $linkType = [string]$item.LinkType
    }

    if ($item.PSObject.Properties.Name -contains "Target" -and $null -ne $item.Target) {
        $rawTarget = if ($item.Target -is [System.Array]) { [string]$item.Target[0] } else { [string]$item.Target }
        if ($rawTarget) {
            $currentTarget = Normalize-Path $rawTarget
        }
    }

    $state = if ($currentTarget -eq $Entry.TargetPath) {
        "linked"
    } elseif ($linkType) {
        "wrong-target"
    } else {
        "exists-not-link"
    }

    return [pscustomobject]@{
        Name = $Entry.Name
        LinkPath = $Entry.LinkPath
        TargetPath = $Entry.TargetPath
        State = $state
        CurrentTarget = $currentTarget
    }
}

function Backup-Conflict {
    param([Parameter(Mandatory = $true)][string]$Path)

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$Path.backup-$timestamp"
    Rename-Item -LiteralPath $Path -NewName (Split-Path $backupPath -Leaf)
    return $backupPath
}

function Ensure-Link {
    param([Parameter(Mandatory = $true)]$Entry)

    $state = Get-LinkState -Entry $Entry
    if ($state.State -eq "linked") {
        return $state
    }

    if ($state.State -ne "missing") {
        if (-not $Force) {
            throw "Refusing to replace '$($Entry.LinkPath)' because it is '$($state.State)'. Re-run with -Force to back it up and replace it."
        }
        $backup = Backup-Conflict -Path $Entry.LinkPath
        Write-Host "Backed up $($Entry.LinkPath) -> $backup"
    }

    $parentDir = Split-Path -Parent $Entry.LinkPath
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    New-Item -ItemType Junction -Path $Entry.LinkPath -Target $Entry.TargetPath | Out-Null
    return Get-LinkState -Entry $Entry
}

function Remove-Link {
    param([Parameter(Mandatory = $true)]$Entry)

    $state = Get-LinkState -Entry $Entry
    if ($state.State -eq "missing") {
        return $state
    }

    if ($state.State -ne "linked") {
        Write-Warning "Skipping unmanaged path: $($Entry.LinkPath) [$($state.State)]"
        return $state
    }

    Remove-Item -LiteralPath $Entry.LinkPath -Force
    return Get-LinkState -Entry $Entry
}

$entries = Get-LinkEntries

switch ($Mode) {
    "status" {
        $entries |
            ForEach-Object { Get-LinkState -Entry $_ } |
            Format-Table Name, State, LinkPath, TargetPath, CurrentTarget -AutoSize
        break
    }
    "install" {
        $entries |
            ForEach-Object { Ensure-Link -Entry $_ } |
            Format-Table Name, State, LinkPath, TargetPath -AutoSize
        Write-Host ""
        Write-Host "User-level install is linked to: $repoRoot"
        Write-Host "Restart Codex after install or after future repo updates."
        break
    }
    "uninstall" {
        $entries |
            ForEach-Object { Remove-Link -Entry $_ } |
            Format-Table Name, State, LinkPath, TargetPath -AutoSize
        break
    }
}
