@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd .

set myRoot=%~dp0..
cd /d %myProjRoot%
:build
kkgenapp %*
set result=%errorlevel%
if NOT %result% == 0 (
	goto :fail
)
echo ** SUCCEEDED **

goto :success
:fail
echo ** FAILED **
:success
popd
exit /b %result%
