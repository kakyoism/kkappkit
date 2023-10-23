@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd .

:: script is at proj_root/ci/
set myProjRoot=%~dp0..
cd /d %myProjRoot%
:build
poetry run python codegen\kkappkit.py -g codegen\kkappkit.kak.json %*
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
