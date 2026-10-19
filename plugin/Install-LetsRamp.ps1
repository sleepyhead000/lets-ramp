#Requires -Version 5.1
<#
.SYNOPSIS
  Installs Let's Ramp into DaVinci Resolve Studio on Windows.

.DESCRIPTION
  Copies LetsRamp.py into Resolve's Scripts\Utility folder (downloading
  it from GitHub first if it is not next to this script). Run it by
  double-clicking Install-LetsRamp.cmd, or:

    powershell -NoProfile -ExecutionPolicy Bypass -File Install-LetsRamp.ps1

  Then restart Resolve Studio and open:
    Workspace > Scripts > Utility > LetsRamp

.PARAMETER Uninstall
  Removes LetsRamp.py from the Utility folder instead of installing.
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$NoElevate
)

$ErrorActionPreference = 'Stop'
$fileName = 'LetsRamp.py'
$githubRaw = 'https://raw.githubusercontent.com/sleepyhead000/lets-ramp/main/plugin/LetsRamp.py'

$utilityFolders = @(
    (Join-Path $env:PROGRAMDATA 'Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility'),
    (Join-Path $env:APPDATA    'Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility')
)

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-ResolveInstall {
    $roots = @(
        (Join-Path $env:PROGRAMFILES 'Blackmagic Design\DaVinci Resolve'),
        (Join-Path ${env:ProgramFiles(x86)} 'Blackmagic Design\DaVinci Resolve')
    ) | Where-Object { $_ -and (Test-Path $_) }
    return [bool]$roots
}

function Get-LetsRampSource {
    # 1) next to this script (offline / extracted-zip case)
    $local = Join-Path $PSScriptRoot $fileName
    if (Test-Path $local) { return $local }

    # 2) download from the GitHub repo
    Write-Host "Not found next to the script - downloading from GitHub..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $tmp = Join-Path $env:TEMP $fileName
    Invoke-WebRequest -Uri $githubRaw -OutFile $tmp -UseBasicParsing
    if (-not (Test-Path $tmp)) { throw 'Download failed.' }
    return $tmp
}

function Assert-LetsRampFile([string]$path) {
    $text = Get-Content -LiteralPath $path -Raw
    if ($text -notmatch "Let's Ramp") {
        throw "'$path' does not look like LetsRamp.py - refusing to install."
    }
}

# --- self-elevate (ProgramData usually needs admin) -------------------------
if (-not $NoElevate -and -not (Test-IsAdmin)) {
    Write-Host 'Administrator rights are needed - requesting elevation...'
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-NoElevate')
    if ($Uninstall) { $argList += '-Uninstall' }
    try {
        Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -Verb RunAs -Wait
        exit 0
    } catch {
        Write-Warning 'Elevation was cancelled - continuing without admin (may fail).'
    }
}

# --- resolve running check --------------------------------------------------
$resolveRunning = [bool](Get-Process -Name 'DaVinci Resolve', 'Resolve' -ErrorAction SilentlyContinue)

try {
    if ($Uninstall) {
        $removed = $false
        foreach ($dir in $utilityFolders) {
            $p = Join-Path $dir $fileName
            if (Test-Path $p) {
                Remove-Item -LiteralPath $p -Force
                Write-Host "Removed: $p"
                $removed = $true
            }
        }
        if (-not $removed) { Write-Host 'Nothing to uninstall - LetsRamp.py is not installed.' }
        if ($resolveRunning) { Write-Host 'Restart DaVinci Resolve for the change to take effect.' }
        exit 0
    }

    Write-Host ''
    Write-Host "Let's Ramp installer" -ForegroundColor Yellow
    Write-Host '===================='
    Write-Host ''

    if (-not (Find-ResolveInstall)) {
        Write-Warning 'DaVinci Resolve does not appear to be installed.'
        $answer = Read-Host 'Install anyway? [y/N]'
        if ($answer -notmatch '^[Yy]') { exit 1 }
    } else {
        Write-Host '[ok] DaVinci Resolve found'
    }

    $source = Get-LetsRampSource
    Assert-LetsRampFile $source
    Write-Host "[ok] Source: $source"

    $destDir = $utilityFolders | Where-Object {
        $parent = Split-Path $_ -Parent
        (Test-Path $parent) -or $_ -eq $utilityFolders[0]
    } | Select-Object -First 1

    # Prefer the folder whose parent exists (correct Resolve version layout)
    foreach ($dir in $utilityFolders) {
        if (Test-Path (Split-Path $dir -Parent)) { $destDir = $dir; break }
    }

    if (-not (Test-Path $destDir)) {
        Write-Host "Creating: $destDir"
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    $dest = Join-Path $destDir $fileName
    Copy-Item -LiteralPath $source -Destination $dest -Force
    Assert-LetsRampFile $dest
    Write-Host "[ok] Installed: $dest"

    Write-Host ''
    Write-Host 'Installed successfully.' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Next steps:'
    if ($resolveRunning) {
        Write-Host '  1. Close and reopen DaVinci Resolve Studio (it is currently running).'
    } else {
        Write-Host '  1. Open DaVinci Resolve Studio.'
    }
    Write-Host '  2. Menu: Workspace > Scripts > Utility > LetsRamp'
    Write-Host '  3. Select a clip on the timeline and pick a preset.'
    Write-Host ''
    Write-Host 'Tip: click "Run diagnostics" in the panel and paste the result'
    Write-Host 'into a GitHub issue - it helps support your Resolve version.'
    Write-Host ''
    Read-Host 'Press Enter to close'
}
catch {
    Write-Host ''
    Write-Host "INSTALL FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ''
    Write-Host 'Manual fallback:'
    Write-Host "  1. Copy $fileName into one of these folders (create it if needed):"
    foreach ($dir in $utilityFolders) { Write-Host "     $dir" }
    Write-Host '  2. Restart Resolve. 3. Workspace > Scripts > Utility > LetsRamp'
    Write-Host ''
    Read-Host 'Press Enter to close'
    exit 1
}
