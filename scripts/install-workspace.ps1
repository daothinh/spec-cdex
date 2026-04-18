[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TargetRepo,

    [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex"),

    [switch]$Force,

    [switch]$NoEnablePlugins
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourceRepo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$marketplacePath = Join-Path $sourceRepo ".agents\plugins\marketplace.json"
$sourceAgentsPath = Join-Path $sourceRepo "AGENTS.md"

function Normalize-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Test-PathInside {
    param(
        [Parameter(Mandatory = $true)][string]$ChildPath,
        [Parameter(Mandatory = $true)][string]$RootPath
    )

    $normalizedChild = Normalize-Path $ChildPath
    $normalizedRoot = (Normalize-Path $RootPath).TrimEnd('\')

    if ([string]::Equals($normalizedChild, $normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    return $normalizedChild.StartsWith("$normalizedRoot\", [System.StringComparison]::OrdinalIgnoreCase)
}

function Remove-LinkPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer) {
        [System.IO.Directory]::Delete($Path)
        return
    }

    [System.IO.File]::Delete($Path)
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $parentDir = Split-Path -Parent $Path
    if ($parentDir) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Get-LinkTargetPath {
    param(
        [Parameter(Mandatory = $true)]$Item,
        [Parameter(Mandatory = $true)][string]$ReferencePath
    )

    if (-not ($Item.PSObject.Properties.Name -contains "Target") -or $null -eq $Item.Target) {
        return $null
    }

    $rawTarget = if ($Item.Target -is [System.Array]) {
        [string]$Item.Target[0]
    } else {
        [string]$Item.Target
    }

    if (-not $rawTarget) {
        return $null
    }

    if (-not [System.IO.Path]::IsPathRooted($rawTarget)) {
        $rawTarget = Join-Path (Split-Path -Parent $ReferencePath) $rawTarget
    }

    return Normalize-Path $rawTarget
}

function Resolve-FinalPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $resolved = Normalize-Path $Path
    $visited = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)

    while ($visited.Add($resolved)) {
        $cursor = $resolved
        $rewritten = $false

        while ($cursor) {
            if (Test-Path -LiteralPath $cursor) {
                $item = Get-Item -LiteralPath $cursor -Force
                $linkTarget = Get-LinkTargetPath -Item $item -ReferencePath $cursor

                if ($linkTarget) {
                    $suffix = $resolved.Substring($cursor.Length).TrimStart('\')
                    $resolved = if ($suffix) {
                        Normalize-Path (Join-Path $linkTarget $suffix)
                    } else {
                        $linkTarget
                    }
                    $rewritten = $true
                    break
                }
            }

            $parent = Split-Path -Parent $cursor
            if (-not $parent -or $parent -eq $cursor) {
                break
            }
            $cursor = $parent
        }

        if (-not $rewritten) {
            break
        }
    }

    return $resolved
}

function Backup-Conflict {
    param([Parameter(Mandatory = $true)][string]$Path)

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$Path.backup-$timestamp"
    Rename-Item -LiteralPath $Path -NewName (Split-Path $backupPath -Leaf)
    return $backupPath
}

function Backup-FileCopy {
    param([Parameter(Mandatory = $true)][string]$Path)

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$Path.backup-$timestamp"
    Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    return $backupPath
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
            CurrentResolvedTarget = $null
        }
    }

    $item = Get-Item -LiteralPath $Entry.LinkPath -Force
    $linkType = ""
    $currentTarget = $null
    $currentResolvedTarget = $null

    if ($item.PSObject.Properties.Name -contains "LinkType") {
        $linkType = [string]$item.LinkType
    }

    if ($item.PSObject.Properties.Name -contains "Target" -and $null -ne $item.Target) {
        $currentTarget = Get-LinkTargetPath -Item $item -ReferencePath $Entry.LinkPath
        if ($currentTarget) {
            $currentResolvedTarget = Resolve-FinalPath $currentTarget
        }
    }

    $desiredResolvedTarget = if (Test-Path -LiteralPath $Entry.TargetPath) {
        Resolve-FinalPath $Entry.TargetPath
    } else {
        Normalize-Path $Entry.TargetPath
    }

    $acceptableResolvedTargets = New-Object System.Collections.Generic.HashSet[string] ([System.StringComparer]::OrdinalIgnoreCase)
    $acceptableResolvedTargets.Add($desiredResolvedTarget) | Out-Null

    if ($Entry.PSObject.Properties.Name -contains "AcceptResolvedTargets" -and $Entry.AcceptResolvedTargets) {
        foreach ($candidate in $Entry.AcceptResolvedTargets) {
            $acceptableResolvedTargets.Add((Normalize-Path $candidate)) | Out-Null
        }
    }

    $state = if (
        $currentTarget -eq $Entry.TargetPath -or
        ($currentResolvedTarget -and $acceptableResolvedTargets.Contains($currentResolvedTarget))
    ) {
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
        CurrentResolvedTarget = $currentResolvedTarget
    }
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

function Get-SourceAgentPrelude {
    $sourceAgents = Get-Content -LiteralPath $sourceAgentsPath -Raw
    $match = [regex]::Match($sourceAgents, '^(?<body>.*?)(?=^## Repository Scope\s*$)', [System.Text.RegularExpressions.RegexOptions]::Singleline -bor [System.Text.RegularExpressions.RegexOptions]::Multiline)

    if ($match.Success) {
        return $match.Groups["body"].Value.Trim()
    }

    return $sourceAgents.Trim()
}

function Extract-LocalAgentContent {
    param([string]$ExistingContent)

    if (-not $ExistingContent) {
        return ""
    }

    $pattern = '<!-- spec-codex-workspace-install:start-local -->\r?\n(?<local>.*?)\r?\n<!-- spec-codex-workspace-install:end-local -->'
    $match = [regex]::Match($ExistingContent, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if ($match.Success) {
        return $match.Groups["local"].Value.Trim()
    }

    return $ExistingContent.Trim()
}

function Render-AgentFile {
    param([AllowEmptyString()][string]$LocalContent = "")

    $parts = @(
        "<!-- spec-codex-workspace-install:generated -->",
        "<!-- source-repo: $sourceRepo -->",
        "",
        (Get-SourceAgentPrelude),
        "",
        "<!-- spec-codex-workspace-install:start-local -->"
    )

    if ($LocalContent) {
        $parts += $LocalContent
    }

    $parts += "<!-- spec-codex-workspace-install:end-local -->"
    return (($parts -join "`r`n").TrimEnd() + "`r`n")
}

function Ensure-AgentFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    $existingContent = if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if ($item.PSIsContainer) {
            if (-not $Force) {
                throw "Refusing to replace directory '$Path' with AGENTS.md file. Re-run with -Force to back it up and replace it."
            }
            $backup = Backup-Conflict -Path $Path
            Write-Host "Backed up $Path -> $backup"
            ""
        } else {
            Get-Content -LiteralPath $Path -Raw
        }
    } else {
        ""
    }

    $rendered = Render-AgentFile -LocalContent (Extract-LocalAgentContent -ExistingContent $existingContent)

    if ($existingContent -ne $rendered) {
        Write-Utf8NoBom -Path $Path -Content $rendered
    }

    return [pscustomobject]@{
        Name = "workspace:AGENTS.md"
        Path = $Path
        State = if ($existingContent -eq $rendered) { "unchanged" } else { "updated" }
    }
}

function Ensure-PluginConfigEnabled {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string[]]$PluginKeys,
        [Parameter(Mandatory = $true)][string]$MarketplaceName
    )

    $original = if (Test-Path -LiteralPath $ConfigPath) {
        Get-Content -LiteralPath $ConfigPath -Raw
    } else {
        ""
    }

    $updated = $original
    $desiredKeys = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($pluginKey in $PluginKeys) {
        $desiredKeys.Add($pluginKey) | Out-Null
    }

    $sectionPattern = '(?ms)^\[plugins\."(?<key>[^"]+)"\]\r?\n(?<body>.*?)(?=^\[|\z)'
    $staleSections = [regex]::Matches($updated, $sectionPattern)
    for ($index = $staleSections.Count - 1; $index -ge 0; $index -= 1) {
        $match = $staleSections[$index]
        $key = $match.Groups["key"].Value
        if ($key -like "*@$MarketplaceName" -and -not $desiredKeys.Contains($key)) {
            $updated = $updated.Remove($match.Index, $match.Length)
        }
    }

    foreach ($pluginKey in $PluginKeys) {
        $sectionHeader = "[plugins.`"$pluginKey`"]"
        $pluginSectionPattern = '(?ms)^\[plugins\."' + [regex]::Escape($pluginKey) + '"\]\r?\n(?<body>.*?)(?=^\[|\z)'
        $match = [regex]::Match($updated, $pluginSectionPattern)

        if ($match.Success) {
            $body = $match.Groups["body"].Value
            $lines = if ($body.Length -gt 0) { $body -split '\r?\n' } else { @() }
            $newLines = New-Object System.Collections.Generic.List[string]
            $enabledWritten = $false

            foreach ($line in $lines) {
                if ($line -match '^\s*enabled\s*=') {
                    if (-not $enabledWritten) {
                        $newLines.Add("enabled = true")
                        $enabledWritten = $true
                    }
                    continue
                }

                if ($line -ne "" -or $newLines.Count -gt 0) {
                    $newLines.Add($line)
                }
            }

            if (-not $enabledWritten) {
                $newLines.Insert(0, "enabled = true")
            }

            $newSection = $sectionHeader + "`r`n" + (($newLines -join "`r`n").TrimEnd()) + "`r`n`r`n"
            $updated = $updated.Substring(0, $match.Index) + $newSection + $updated.Substring($match.Index + $match.Length)
            continue
        }

        if ($updated -and -not $updated.EndsWith("`n")) {
            $updated += "`r`n"
        }
        if ($updated.Trim()) {
            $updated += "`r`n"
        }
        $updated += $sectionHeader + "`r`nenabled = true`r`n"
    }

    if ($updated) {
        $updated = $updated.TrimEnd("`r", "`n") + "`r`n"
    }

    if ($updated -ne $original) {
        if (Test-Path -LiteralPath $ConfigPath) {
            $backup = Backup-FileCopy -Path $ConfigPath
            Write-Host "Backed up $ConfigPath -> $backup"
        }
        Write-Utf8NoBom -Path $ConfigPath -Content $updated
    }

    return [pscustomobject]@{
        Path = $ConfigPath
        State = if ($updated -eq $original) { "unchanged" } else { "updated" }
    }
}

function Remove-ManagedLink {
    param([Parameter(Mandatory = $true)]$Entry)

    if (-not (Test-Path -LiteralPath $Entry.LinkPath)) {
        return [pscustomobject]@{
            Name = $Entry.Name
            State = "missing"
            LinkPath = $Entry.LinkPath
            TargetPath = $Entry.TargetPath
        }
    }

    $item = Get-Item -LiteralPath $Entry.LinkPath -Force
    $linkType = if ($item.PSObject.Properties.Name -contains "LinkType") { [string]$item.LinkType } else { "" }
    if (-not $linkType) {
        return [pscustomobject]@{
            Name = $Entry.Name
            State = "exists-not-link"
            LinkPath = $Entry.LinkPath
            TargetPath = $Entry.TargetPath
        }
    }

    Remove-LinkPath -Path $Entry.LinkPath

    return [pscustomobject]@{
        Name = $Entry.Name
        State = "removed"
        LinkPath = $Entry.LinkPath
        TargetPath = $Entry.TargetPath
    }
}

if (-not (Test-Path -LiteralPath $TargetRepo -PathType Container)) {
    throw "Target repo does not exist or is not a directory: $TargetRepo"
}

if (-not (Test-Path -LiteralPath $marketplacePath -PathType Leaf)) {
    throw "Missing Codex marketplace manifest: $marketplacePath"
}

$targetRepo = Normalize-Path $TargetRepo
$codexHome = Normalize-Path $CodexHome
$marketplace = Get-Content -LiteralPath $marketplacePath -Raw | ConvertFrom-Json

$workspaceEntries = @(
    [pscustomobject]@{
        Name = "workspace:.agents\plugins"
        LinkPath = (Normalize-Path (Join-Path $targetRepo ".agents\plugins"))
        TargetPath = (Normalize-Path (Join-Path $sourceRepo ".agents\plugins"))
    },
    [pscustomobject]@{
        Name = "workspace:plugins"
        LinkPath = (Normalize-Path (Join-Path $targetRepo "plugins"))
        TargetPath = (Normalize-Path (Join-Path $sourceRepo "plugins"))
    },
    [pscustomobject]@{
        Name = "workspace:skills"
        LinkPath = (Normalize-Path (Join-Path $targetRepo "skills"))
        TargetPath = (Normalize-Path (Join-Path $sourceRepo "skills"))
    }
)

$workspaceResults = $workspaceEntries | ForEach-Object { Ensure-Link -Entry $_ }
$agentResult = Ensure-AgentFile -Path (Normalize-Path (Join-Path $targetRepo "AGENTS.md"))

$pluginResults = @()
$configResult = $null

if (-not $NoEnablePlugins) {
    $pluginEntries = foreach ($plugin in $marketplace.plugins) {
        $sourcePath = ($plugin.source.path -replace "^[.][/\\]", "") -replace "/", "\"
        $pluginDir = Split-Path $sourcePath -Leaf
        $sourcePluginPath = Normalize-Path (Join-Path $sourceRepo $sourcePath)
        [pscustomobject]@{
            Name = "codex-plugin:$($plugin.name)"
            LinkPath = (Normalize-Path (Join-Path $codexHome "plugins\$pluginDir"))
            TargetPath = (Normalize-Path (Join-Path $targetRepo $sourcePath))
            AcceptResolvedTargets = @($sourcePluginPath)
        }
    }

    $pluginResults = $pluginEntries | ForEach-Object { Ensure-Link -Entry $_ }

    try {
        $desiredPluginNames = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in $pluginEntries) {
            $desiredPluginNames.Add((Split-Path -Leaf $entry.LinkPath)) | Out-Null
        }
    } catch {
        throw "Failed to compute desired plugin names: $($_.Exception.Message)"
    }

    try {
        $stalePluginEntries = @()
        $pluginsRoot = Normalize-Path (Join-Path $codexHome "plugins")
        $managedRoots = @(
            (Normalize-Path (Join-Path $targetRepo "plugins")).TrimEnd('\'),
            (Normalize-Path (Join-Path $sourceRepo "plugins")).TrimEnd('\')
        )

        if (Test-Path -LiteralPath $pluginsRoot -PathType Container) {
            foreach ($item in Get-ChildItem -LiteralPath $pluginsRoot -Force) {
                $pluginName = $item.Name
                if ($desiredPluginNames.Contains($pluginName)) {
                    continue
                }

                $currentTarget = Get-LinkTargetPath -Item $item -ReferencePath $item.FullName
                $currentResolvedTarget = if ($currentTarget) { Resolve-FinalPath $currentTarget } else { $null }
                $targetCandidate = if ($currentResolvedTarget) { [string]$currentResolvedTarget } else { [string]$currentTarget }
                if (-not $targetCandidate) {
                    continue
                }

                $normalizedTarget = Normalize-Path $targetCandidate
                $isManaged = $false
                foreach ($managedRoot in $managedRoots) {
                    if (
                        [string]::Equals($normalizedTarget, $managedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
                        $normalizedTarget.StartsWith("$managedRoot\", [System.StringComparison]::OrdinalIgnoreCase)
                    ) {
                        $isManaged = $true
                        break
                    }
                }

                if (-not $isManaged) {
                    continue
                }

                $stalePluginEntries += [pscustomobject]@{
                    Name = "stale-codex-plugin:$pluginName"
                    LinkPath = $item.FullName
                    TargetPath = $targetCandidate
                }
            }
        }
    } catch {
        throw "Failed to identify stale plugin links: $($_.Exception.Message)"
    }

    try {
        $stalePluginResults = @(
            $stalePluginEntries |
                ForEach-Object { Remove-ManagedLink -Entry $_ }
        )
    } catch {
        throw "Failed to remove stale plugin links: $($_.Exception.Message)"
    }

    $pluginKeys = @($marketplace.plugins | ForEach-Object { "$($_.name)@$($marketplace.name)" })
    try {
        $configResult = Ensure-PluginConfigEnabled `
            -ConfigPath (Normalize-Path (Join-Path $codexHome "config.toml")) `
            -PluginKeys $pluginKeys `
            -MarketplaceName $marketplace.name
    } catch {
        throw "Failed to sync Codex config: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "Workspace links:"
$workspaceResults | Format-Table Name, State, LinkPath, TargetPath -AutoSize

Write-Host ""
Write-Host "AGENTS merge:"
$agentResult | Format-Table Name, State, Path -AutoSize

if (-not $NoEnablePlugins) {
    Write-Host ""
    Write-Host "Codex plugin links:"
    $pluginResults | Format-Table Name, State, LinkPath, TargetPath -AutoSize

    if ($stalePluginResults.Count -gt 0) {
        Write-Host ""
        Write-Host "Removed stale managed plugin links:"
        $stalePluginResults | Format-Table Name, State, LinkPath, TargetPath -AutoSize
    }

    Write-Host ""
    Write-Host "Codex config:"
    $configResult | Format-Table Path, State -AutoSize
}

Write-Host ""
Write-Host "Target workspace prepared at: $targetRepo"
if (-not $NoEnablePlugins) {
    Write-Host "Plugins enabled from marketplace '$($marketplace.name)': $($marketplace.plugins.Count)"
}
Write-Host "Restart Codex before opening the target workspace."
