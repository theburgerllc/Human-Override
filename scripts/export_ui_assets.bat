@echo off
setlocal enabledelayedexpansion

set "PREV_INKSCAPE=%INKSCAPE%"
call "%~dp0_config.bat"
if defined PREV_INKSCAPE set "INKSCAPE=%PREV_INKSCAPE%"

set SVG_DIR=%REPO_ROOT%\assets\ui\svg
set PNG_DIR=%REPO_ROOT%\assets\ui\png

if not exist "%PNG_DIR%" mkdir "%PNG_DIR%"

echo Exporting UI assets...
for %%F in ("%SVG_DIR%\*.svg") do (
  set NAME=%%~nF
  set OUT=%PNG_DIR%\!NAME!.png

  "%INKSCAPE%" "%%F" ^
    --export-type=png ^
    --export-filename="!OUT!" ^
    --export-area-page ^
    --export-background-opacity=0 ^
    --export-width=1080

  if errorlevel 1 (
    echo FAILED: %%F
    exit /b 1
  ) else (
    echo OK: !NAME!.png
  )
)

echo Done.
exit /b 0
