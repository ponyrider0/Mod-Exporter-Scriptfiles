@echo off
REM =============================================================
REM Modify the set PYTHONEXE=... line below to point to your
REM python executable. Double-quotes must go around the
REM entire statement. ex: set "PYTHONEXE=C:\python26\python.exe"
REM
REM =============================================================

set "PYTHONEXE=C:\Python26\python.exe"
REM set "BLENDEREXE=C:\Program Files (x86)\Blender Foundation\Blender\blender.exe"
set "BLENDEREXE=C:\Blender\blender.exe"

"%PYTHONEXE%" modexporter_blender_main.py

echo "Blender conversion complete.  Press any key to close window."
pause
