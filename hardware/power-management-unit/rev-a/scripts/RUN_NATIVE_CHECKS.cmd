@echo off
setlocal
rem Run from the normal Windows user session. No elevated privileges needed.
rem The Python runner records the actual native ERC/DRC process exit codes.
set "PMU_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PMU_PYTHON%" (
  echo Python runtime not found. Run run_native_checks.py with Python 3.
  pause
  exit /b 2
)
"%PMU_PYTHON%" "%~dp0run_native_checks.py" --kicad-root "%ProgramFiles%\KiCad\10.0" --timeout 180
set "PMU_CHECK_RESULT=%ERRORLEVEL%"
echo.
echo PMU native check runner exit code: %PMU_CHECK_RESULT%
echo Reports: %~dp0..\reports\native-checks-both.json
pause
exit /b %PMU_CHECK_RESULT%
