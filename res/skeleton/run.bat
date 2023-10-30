@echo off
setlocal EnableExtensions DisableDelayedExpansion
:: protect cwd
pushd

cd /d %~dp0
poetry run python src\cli.py %*
if NOT %errorlevel% == 0 (
	goto :fail
)
popd
goto :EOF

:fail
popd
