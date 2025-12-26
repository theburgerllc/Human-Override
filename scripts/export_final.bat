@echo off
setlocal enabledelayedexpansion

call "%~dp0_config.bat"

if "%~1"=="" (
  echo Usage: export_final.bat S01E01
  exit /b 1
)

set EP=%~1
set RENDER_DIR=%REPO_ROOT%\renders\season01_housing_mode\%EP%
set IN_MP4=%RENDER_DIR%\edit_export.mp4
set SRT=%RENDER_DIR%\captions.srt
set OUT_CLEAN=%RENDER_DIR%\final_clean.mp4
set OUT_BURN=%RENDER_DIR%\final_burned.mp4

if not exist "%IN_MP4%" (
  echo Missing: %IN_MP4%
  exit /b 1
)

"%FFMPEG%" -y -i "%IN_MP4%" ^
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" ^
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" ^
  -c:v libx264 -preset medium -crf 18 ^
  -c:a aac -b:a 192k ^
  "%OUT_CLEAN%"

if errorlevel 1 exit /b 1

if exist "%SRT%" (
  "%FFMPEG%" -y -i "%OUT_CLEAN%" ^
    -vf "subtitles='%SRT%':force_style='FontName=Arial,FontSize=52,Outline=3,Shadow=1,MarginV=90'" ^
    -c:v libx264 -preset medium -crf 18 ^
    -c:a copy ^
    "%OUT_BURN%"

  if errorlevel 1 exit /b 1
)

exit /b 0
