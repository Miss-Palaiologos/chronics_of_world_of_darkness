@echo off
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%chronicles\the-unlisted\src"
"%ROOT%.venv\Scripts\python.exe" -m the_unlisted.cli gui
