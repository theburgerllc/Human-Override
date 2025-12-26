@echo off
setlocal

set REPO_ROOT=%~dp0..

if not exist "%REPO_ROOT%\.venv" (
  python -m venv "%REPO_ROOT%\.venv"
)

call "%REPO_ROOT%\.venv\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r "%REPO_ROOT%\tools\requirements.txt"

echo.
echo Done. Activate with:
echo   call "%REPO_ROOT%\.venv\Scripts\activate.bat"
echo.
exit /b 0
