@echo off
setlocal
echo Checking environment prerequisites...
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe tools\diagnostics.py
) else if exist "C:\Tools\venvs\the-human\Scripts\python.exe" (
    "C:\Tools\venvs\the-human\Scripts\python.exe" tools\diagnostics.py
) else (
    python tools\diagnostics.py
)
if errorlevel 1 goto fail

echo.
echo For a full production run, ensure RESOLVED values point to valid executables.
exit /b 0

:fail
echo Diagnostics failed.
exit /b 1
