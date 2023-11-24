@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd .

:: see posix version for details

set myRoot=%~dp0..
:build
kkappgen -r %myRoot% %*
set result=%errorlevel%
if NOT %result% == 0 (
	goto :failed
)
echo ** SUCCEEDED **
goto :passed

:failed
echo ** FAILED **
:passed
popd
exit /b %result%
