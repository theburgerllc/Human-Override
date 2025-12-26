@echo off
setlocal enabledelayedexpansion

REM ==========================================================
REM make_all.bat
REM One command to:
REM  1) generate UI SVGs (incl. specular sweep asset)
REM  2) export SVG -> PNG
REM  3) validate episode YAML (strict)
REM  4) render animatic
REM  5) generate thumbnail
REM  6) generate shorts (3 variants)
REM ==========================================================

if "%~1"=="" (
  echo Usage: scripts\make_all.bat ^<episode_yaml^> ^<episode_id^>
  echo Example: scripts\make_all.bat episodes\season01_housing_mode\ep01.yaml S01E01
  exit /b 1
)
if "%~2"=="" (
  echo Missing episode_id.
  exit /b 1
)

set EPYAML=%~1
set EPID=%~2

REM Ensure venv exists
if not exist .venv\Scripts\python.exe (
  if exist scripts\setup_venv_windows.bat (
    call scripts\setup_venv_windows.bat
  )
)

set PY=.venv\Scripts\python.exe
if not exist %PY% (
  if exist "C:\Tools\venvs\the-human\Scripts\python.exe" (
    set PY="C:\Tools\venvs\the-human\Scripts\python.exe"
  ) else (
    set PY=python
  )
)

echo ==========================================================
echo [1/6] Generate UI SVG overlays (force ensures fx asset updates)
echo ==========================================================
%PY% -m tools.gen_ui_svgs --force
if errorlevel 1 exit /b 1

echo ==========================================================
echo [2/6] Export UI assets (SVG->PNG)
echo ==========================================================
call scripts\export_ui_assets.bat
if errorlevel 1 (
  if "%USE_MOCKS%"=="1" (
    echo [WARN] Export failed. Falling back to MOCK assets because USE_MOCKS=1...
    call scripts\mock_ui_assets.bat
    if errorlevel 1 exit /b 1
  ) else (
    echo [ERROR] Export failed. Real Inkscape is required.
    echo Set USE_MOCKS=1 if you intended to run in a mock environment.
    exit /b 1
  )
)

echo ==========================================================
echo [3/6] Validate episode YAML (strict)
echo ==========================================================
%PY% -m tools.validate_episode --episode-yaml "%EPYAML%" --strict
if errorlevel 1 exit /b 1

echo ==========================================================
echo [4/6] Render animatic
echo ==========================================================
%PY% -m tools.tho animatic %EPID% --episode-yaml "%EPYAML%" --run
if errorlevel 1 exit /b 1

echo ==========================================================
echo [5/6] Generate thumbnail (16:9)
echo ==========================================================
%PY% -m tools.thumb --episode-yaml "%EPYAML%" --episode-id %EPID%
if errorlevel 1 exit /b 1

echo ==========================================================
echo [6/6] Generate Shorts (3 variants)
echo ==========================================================
%PY% -m tools.shorts --episode-yaml "%EPYAML%" --episode-id %EPID% --target-seconds 35
if errorlevel 1 exit /b 1

echo ==========================================================
echo DONE: animatic + thumbnail + shorts are generated.
echo ==========================================================
exit /b 0
