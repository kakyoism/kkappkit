@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd

:: see posix version for details

cd /d %~dp0
cscript //nologo "ci\_ui.vbs" "ci\_ui.bat" %*
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
