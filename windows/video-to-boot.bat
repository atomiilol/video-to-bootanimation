@echo off
setlocal DisableDelayedExpansion
if "%~1"=="" goto usage
where py >nul 2>nul
if errorlevel 1 goto python
py -3 "%~dp0converter.py" video-to-boot %*
exit /b %errorlevel%
:python
where python >nul 2>nul
if errorlevel 1 goto missing
python "%~dp0converter.py" video-to-boot %*
exit /b %errorlevel%
:missing
echo Python 3.9 or newer is required. Install it from python.org and enable PATH.
pause
exit /b 1
:usage
echo Usage: video-to-boot.bat "input file" ["output file"] [options]
echo You can also drag a file onto this batch file.
pause
exit /b 1
