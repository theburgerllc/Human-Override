@echo off
setlocal enabledelayedexpansion
call "%~dp0_config.bat"

REM Fallback if Inkscape is missing: Use FFmpeg to generate placeholder PNGs
set SVG_DIR=%REPO_ROOT%\assets\ui\svg
set PNG_DIR=%REPO_ROOT%\assets\ui\png

if not exist "%PNG_DIR%" mkdir "%PNG_DIR%"

echo [WARN] Inkscape missing/failed. Gnerating MOCK assets using FFmpeg...

for %%F in ("%SVG_DIR%\*.svg") do (
  set NAME=%%~nF
  set OUT=%PNG_DIR%\!NAME!.png
  
  if not exist "!OUT!" (
    REM Generate a semitransparent blue placeholder 1080x1920
    "%FFMPEG%" -y -hide_banner -loglevel error ^
      -f lavfi -i "color=c=blue@0.5:s=1080x1920" ^
      -frames:v 1 "!OUT!"
      
    echo MOCKED: !NAME!.png
  )
)
exit /b 0
