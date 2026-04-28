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
$installUserLevelScript = Join-Path $PSScriptRoot "install-user-level.ps1"
$sourceAgentsDir = Join-Path $repoRoot ".codex\agents"
$destAgentsDir = Join-Path $CodexHome "agents"
$manifestDir = Join-Path $CodexHome ".workersio"
$manifestPath = Join-Path $manifestDir "security-sync-agents.json"

function Normalize-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Get-FileHashValue {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Backup-Path {
    param([Parameter(Mandatory = $true)][string]$Path)

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$Path.backup-$timestamp"
    Rename-Item -LiteralPath $Path -NewName (Split-Path $backupPath -Leaf)
    return $backupPath
}

function Load-Manifest {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        return [pscustomobject]@{
            repoRoot = (Normalize-Path $repoRoot)
            files = @()
        }
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if (-not $manifest.PSObject.Properties.Name.Contains("files")) {
        $manifest | Add-Member -NotePropertyName files -NotePropertyValue @()
    }
    return $manifest
}

function Save-Manifest {
    param([Parameter(Mandatory = $true)]$Entries)

    Ensure-Directory -Path $manifestDir

    $manifest = [pscustomobject]@{
        repoRoot = (Normalize-Path $repoRoot)
        syncedAt = (Get-Date).ToString("o")
        files = @(
            $Entries | ForEach-Object {
                [pscustomobject]@{
                    name = $_.Name
                    destination = $_.DestPath
                    hash = $_.SourceHash
                }
            }
        )
    }

    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}

function Get-ManifestLookup {
    param([Parameter(Mandatory = $true)]$Manifest)

    $lookup = @{}
    foreach ($item in @($Manifest.files)) {
        $lookup[[string]$item.name] = $item
    }
    return $lookup
}

function Get-DesiredAgents {
    if (-not (Test-Path -LiteralPath $sourceAgentsDir -PathType Container)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $sourceAgentsDir -Filter "*.toml" -File |
            Sort-Object Name |
            ForEach-Object {
                [pscustomobject]@{
                    Name = $_.Name
                    SourcePath = (Normalize-Path $_.FullName)
                    DestPath = (Normalize-Path (Join-Path $destAgentsDir $_.Name))
                    SourceHash = (Get-FileHashValue -Path $_.FullName)
                }
            }
    )
}

function Get-StaleManagedAgents {
    param(
        [Parameter(Mandatory = $true)]$Manifest,
        [Parameter(Mandatory = $true)][object[]]$DesiredEntries
    )

    $desiredNames = @{}
    foreach ($entry in $DesiredEntries) {
        $desiredNames[$entry.Name] = $true
    }

    $stale = @()
    foreach ($item in @($Manifest.files)) {
        if ($desiredNames.ContainsKey([string]$item.name)) {
            continue
        }

        $stale += [pscustomobject]@{
            Name = [string]$item.name
            DestPath = Normalize-Path (Join-Path $destAgentsDir ([string]$item.name))
            RecordedHash = [string]$item.hash
        }
    }

    return @($stale)
}

function Get-AgentStatusRows {
    param(
        [Parameter(Mandatory = $true)][object[]]$DesiredEntries,
        [Parameter(Mandatory = $true)]$ManifestLookup,
        [object[]]$StaleEntries = @()
    )

    $rows = @()

    foreach ($entry in $DesiredEntries) {
        $destHash = Get-FileHashValue -Path $entry.DestPath
        $state = "missing"

        if ($destHash -eq $entry.SourceHash) {
            $state = "current"
        } elseif ($null -ne $destHash) {
            if ($ManifestLookup.ContainsKey($entry.Name)) {
                $recordedHash = [string]$ManifestLookup[$entry.Name].hash
                if ($destHash -eq $recordedHash) {
                    $state = "outdated"
                } else {
                    $state = "modified"
                }
            } else {
                $state = "conflict"
            }
        }

        $rows += [pscustomobject]@{
            Name = $entry.Name
            State = $state
            Destination = $entry.DestPath
            Source = $entry.SourcePath
        }
    }

    foreach ($entry in @($StaleEntries)) {
        $state = if (Test-Path -LiteralPath $entry.DestPath -PathType Leaf) { "stale-managed" } else { "removed" }
        $rows += [pscustomobject]@{
            Name = $entry.Name
            State = $state
            Destination = $entry.DestPath
            Source = "(removed from repo)"
        }
    }

    return $rows
}

function Invoke-PluginSync {
    param([Parameter(Mandatory = $true)][ValidateSet("install", "status", "uninstall")][string]$RequestedMode)

    & $installUserLevelScript -Mode $RequestedMode -CodexHome $CodexHome -Force:$Force
}

$manifest = Load-Manifest
$manifestLookup = Get-ManifestLookup -Manifest $manifest
$desiredAgents = @(Get-DesiredAgents)
$staleAgents = @(Get-StaleManagedAgents -Manifest $manifest -DesiredEntries $desiredAgents)

switch ($Mode) {
    "status" {
        Invoke-PluginSync -RequestedMode status
        Write-Host ""
        Write-Host "Security agent sync status:"
        Get-AgentStatusRows -DesiredEntries $desiredAgents -ManifestLookup $manifestLookup -StaleEntries $staleAgents |
            Format-Table Name, State, Destination, Source -AutoSize
        break
    }
    "install" {
        Invoke-PluginSync -RequestedMode install

        Ensure-Directory -Path $destAgentsDir
        $results = @()

        foreach ($entry in $desiredAgents) {
            $destExists = Test-Path -LiteralPath $entry.DestPath -PathType Leaf
            $destHash = Get-FileHashValue -Path $entry.DestPath
            $state = "copied"

            if ($destHash -eq $entry.SourceHash) {
                $state = "unchanged"
            } elseif ($destExists) {
                if ($manifestLookup.ContainsKey($entry.Name)) {
                    $recordedHash = [string]$manifestLookup[$entry.Name].hash
                    if ($destHash -ne $recordedHash) {
                        if (-not $Force) {
                            throw "Refusing to overwrite modified managed agent '$($entry.DestPath)'. Re-run with -Force to back it up and replace it."
                        }

                        $backup = Backup-Path -Path $entry.DestPath
                        Write-Host "Backed up $($entry.DestPath) -> $backup"
                    }
                } else {
                    if (-not $Force) {
                        throw "Refusing to replace unmanaged agent '$($entry.DestPath)'. Re-run with -Force to back it up and replace it."
                    }

                    $backup = Backup-Path -Path $entry.DestPath
                    Write-Host "Backed up $($entry.DestPath) -> $backup"
                }

                $state = "updated"
            }

            if ($state -ne "unchanged") {
                Copy-Item -LiteralPath $entry.SourcePath -Destination $entry.DestPath -Force
            }

            $results += [pscustomobject]@{
                Name = $entry.Name
                State = $state
                Destination = $entry.DestPath
            }
        }

        foreach ($entry in $staleAgents) {
            if (-not (Test-Path -LiteralPath $entry.DestPath -PathType Leaf)) {
                continue
            }

            $destHash = Get-FileHashValue -Path $entry.DestPath
            if ($destHash -ne $entry.RecordedHash) {
                if (-not $Force) {
                    Write-Warning "Skipping modified stale managed agent: $($entry.DestPath)"
                    continue
                }

                $backup = Backup-Path -Path $entry.DestPath
                Write-Host "Backed up $($entry.DestPath) -> $backup"
            }

            Remove-Item -LiteralPath $entry.DestPath -Force
            $results += [pscustomobject]@{
                Name = $entry.Name
                State = "removed-stale"
                Destination = $entry.DestPath
            }
        }

        Save-Manifest -Entries $desiredAgents

        Write-Host ""
        Write-Host "Security agents synced to: $destAgentsDir"
        $results | Format-Table Name, State, Destination -AutoSize
        Write-Host ""
        Write-Host "Restart Codex after sync or after future repo updates."
        break
    }
    "uninstall" {
        $results = @()

        foreach ($item in @($manifest.files)) {
            $destPath = Normalize-Path (Join-Path $destAgentsDir ([string]$item.name))
            if (-not (Test-Path -LiteralPath $destPath -PathType Leaf)) {
                $results += [pscustomobject]@{
                    Name = [string]$item.name
                    State = "missing"
                    Destination = $destPath
                }
                continue
            }

            $destHash = Get-FileHashValue -Path $destPath
            if ($destHash -ne [string]$item.hash) {
                if (-not $Force) {
                    Write-Warning "Skipping modified managed agent: $destPath"
                    $results += [pscustomobject]@{
                        Name = [string]$item.name
                        State = "modified-skip"
                        Destination = $destPath
                    }
                    continue
                }

                $backup = Backup-Path -Path $destPath
                Write-Host "Backed up $destPath -> $backup"
            }

            Remove-Item -LiteralPath $destPath -Force
            $results += [pscustomobject]@{
                Name = [string]$item.name
                State = "removed"
                Destination = $destPath
            }
        }

        if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
            Remove-Item -LiteralPath $manifestPath -Force
        }

        if (Test-Path -LiteralPath $manifestDir -PathType Container) {
            $remaining = @(Get-ChildItem -LiteralPath $manifestDir -Force)
            if ($remaining.Count -eq 0) {
                Remove-Item -LiteralPath $manifestDir -Force
            }
        }

        Invoke-PluginSync -RequestedMode uninstall
        Write-Host ""
        Write-Host "Security agents removed from: $destAgentsDir"
        $results | Format-Table Name, State, Destination -AutoSize
        break
    }
}
