@echo off
setlocal EnableExtensions DisableDelayedExpansion

pushd

:: Use PowerShell to resolve the actual path of the batch file
for /f "delims=" %%i in ('powershell -Command "Get-Item -LiteralPath '%~f0' | Select-Object -ExpandProperty Target"') do set "BatchPath=%%~dpi"

:: If the batch file is not a symlink, use its own path
if "%BatchPath%"=="" set "BatchPath=%~dp0"

:: Change to the directory of the original batch file
cd /d "%BatchPath%"
poetry run python src\cli.py %*
if NOT %errorlevel% == 0 (
	goto :fail
)
popd
goto :EOF

:fail
popd
