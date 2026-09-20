$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root 'chronicles\the-unlisted\src'
$python = Join-Path $root '.venv\Scripts\python.exe'

& $python -m the_unlisted.cli gui
