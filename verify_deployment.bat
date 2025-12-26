@echo off
REM Ensure mock mode is NOT enabled
set USE_MOCKS=

REM Clean outputs to avoid false positives
if exist outputs rmdir /s /q outputs

REM Preflight (must PASS)
call scripts\check_prereqs.bat
if errorlevel 1 (
    echo prereqs_exit=FAIL
    exit /b 1
)
echo prereqs_exit=PASS

REM Run unit tests
python -m pytest -q
if errorlevel 1 (
    echo pytest_exit=FAIL
    exit /b 1
)
echo pytest_exit=PASS

REM Full pipeline (REAL tools)
call scripts\make_all.bat episodes\season01_housing_mode\ep01.yaml S01E01
if errorlevel 1 (
    echo make_all_exit=FAIL
    exit /b 1
)
echo make_all_exit=PASS
