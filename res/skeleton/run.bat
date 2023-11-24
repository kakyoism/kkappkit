@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd

:: see posix version for details

cd /d %~dp0
poetry run python src\cli.py %*
set result=%errorlevel%
if NOT %result% == 0 (
	goto :failed
)
goto :passed

:failed
echo ** FAILED **
:passed
popd
exit /b %result%
