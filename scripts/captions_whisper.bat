@echo off
setlocal enabledelayedexpansion

call "%~dp0_config.bat"

if "%~1"=="" (
  echo Usage: captions_whisper.bat S01E01
  exit /b 1
)

set EP=%~1
set RENDER_DIR=%REPO_ROOT%\renders\season01_housing_mode\%EP%
set VO_IN=%RENDER_DIR%\vo_mix.wav
set TMP_WAV=%RENDER_DIR%\_tmp_16k_mono.wav
set OUT_BASE=%RENDER_DIR%\captions

if not exist "%RENDER_DIR%" (
  echo Missing folder: %RENDER_DIR%
  exit /b 1
)

if not exist "%VO_IN%" (
  echo Missing VO file: %VO_IN%
  exit /b 1
)

"%FFMPEG%" -y -i "%VO_IN%" -ar 16000 -ac 1 "%TMP_WAV%"
if errorlevel 1 exit /b 1

"%WHISPER_EXE%" -m "%WHISPER_MODEL%" -f "%TMP_WAV%" -osrt -of "%OUT_BASE%" -l en
if errorlevel 1 exit /b 1

if exist "%OUT_BASE%.srt" (
  move /Y "%OUT_BASE%.srt" "%RENDER_DIR%\captions.srt" >nul
)

del /Q "%TMP_WAV%" >nul 2>&1

echo Captions created: %RENDER_DIR%\captions.srt
exit /b 0
