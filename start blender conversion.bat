@echo off
REM =============================================================
REM Modify the set PYTHONEXE=... line below to point to your
REM python executable. Double-quotes must go around the
REM entire statement. ex: set "PYTHONEXE=C:\python26\python.exe"
REM
REM =============================================================

set "PYTHONEXE=C:\Python26\python.exe"
set "BLENDEREXE=C:\Program Files (x86)\Blender Foundation\Blender\blender.exe"

setlocal enableextensions
set outputdir=c:/oblivion.output/jobs
set count=0
for %%x in (%outputdir%/*.job) do set /a count+=1
if %count% == 0 goto done
set locks=0
for %%x in (%outputdir%\*.lock) do set /a locks+=1
if %locks% NEQ 0 goto warning
goto skipwarning

:warning
echo.
echo ----------------------------------------------
echo.
echo (%locks%) Lock file detected!
echo.
echo If you recently crashed, then please run the
echo "cleanup blender conversion crash.bat".
echo.
echo Unless you know what you are doing, press
echo CTRL-C now and quit! Proceed at your own risk!
echo.
echo ----------------------------------------------
pause

:skipwarning
echo.
echo ----------------------------------------------
echo.
echo Total jobs found = %count%
echo Press any key to start jobs.
echo.
echo ----------------------------------------------
echo.
pause

:loop
rem echo "%PYTHONEXE%" modexporter_blender_main.py "%BLENDEREXE%"
"%PYTHONEXE%" modexporter_blender_main.py "%BLENDEREXE%"
set count=0
for %%x in (%outputdir%/*.job) do set /a count+=1
set locks=0
for %%x in (%outputdir%\*.lock) do set /a locks+=1
set /a "jobs=%count%-%locks%"
echo Number of jobs left = %jobs%
if %jobs% gtr 0 goto loop

endlocal

:done
echo.
echo ----------------------------------------------
echo.
echo Jobs completed. Press any key to close window.
echo.
echo ----------------------------------------------
echo.
pause
rem c:\python27\python.exe c:\python27\scripts\niftoaster.py optimize c:\oblivion.out\data\meshes
rem pause
