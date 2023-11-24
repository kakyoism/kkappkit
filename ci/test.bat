@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd .

:: see posix version for details

cd /d %~dp0../test
poetry run coverage run --omit '*virtualenvs*' -m pytest
set result=%errorlevel%
poetry run coverage report -m
if NOT %result% == 0 (
	goto :failed
)
goto :passed

:failed
echo ** FAILED **
:passed
popd
exit /b %result%
