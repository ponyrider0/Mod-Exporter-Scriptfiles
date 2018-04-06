@echo off
setlocal enableextensions
set outputdir=c:\oblivion.output\jobs

set count=0
for %%x in (%outputdir%\*.job) do set /a count+=1
set locks=0
for %%x in (%outputdir%\*.lock) do set /a locks+=1
rem if %locks% == 0 goto nocleanup

:cleanup
echo.
echo ----------------------------------------------
echo Total jobs found = %count%
echo Total locks found = %locks%
echo.
echo Press any key to cleanup completed jobs and delete locks.
echo.
echo ----------------------------------------------
echo.
pause
rename %outputdir%\*.done *.old
del %outputdir%\*.lock
echo.
echo.
echo ----------------------------------------------
echo.
echo Cleanup completed. Press any key to close window.
echo.
echo ----------------------------------------------
echo.
pause
goto end

:nocleanup
echo.
echo ----------------------------------------------
echo Total jobs found = %count%
echo No locks found, no cleanup necessary.
echo.
echo Press any key to close window.
echo ----------------------------------------------
echo.
pause


:end
endlocal
