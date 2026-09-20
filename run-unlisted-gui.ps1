$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root 'chronicles\the-unlisted\src'
$venv = Join-Path $root '.venv\Scripts\python.exe'

function Test-Tk([string]$exe) {
    if (-not (Test-Path -LiteralPath $exe)) { return $false }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $null = & $exe -c "import tkinter; tkinter.Tk().destroy()" 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $prev
    }
}

$candidates = @()
if ($env:CHRONICS_PYTHON) { $candidates += $env:CHRONICS_PYTHON }
$candidates += $venv
foreach ($name in @('python', 'python3', 'py')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
}

$python = $candidates | Where-Object { Test-Tk $_ } | Select-Object -First 1

if (-not $python) {
    Write-Host 'No Python with a working Tcl/Tk was found.' -ForegroundColor Yellow
    Write-Host 'The uv-managed CPython ships without usable Tcl/Tk; the GUI needs a python.org or conda interpreter.'
    Write-Host 'Point the script at one and retry:'
    Write-Host '  $env:CHRONICS_PYTHON = "C:\path\to\python.exe"; .\run-unlisted-gui.ps1'
    Write-Host 'CLI usage is unaffected: uv run the-unlisted check'
    exit 1
}

# Launching from a non-uv interpreter: point PYTHONPATH at this chronicle's source.
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$src;$env:PYTHONPATH" } else { $src }

Write-Host "Using interpreter: $python"
& $python -m the_unlisted.cli gui
