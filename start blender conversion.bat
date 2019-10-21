@echo off
REM =============================================================
REM Modify the set PYTHONEXE=... line below to point to your
REM python executable. Double-quotes must go around the
REM entire statement. ex: set "PYTHONEXE=C:\python26\python.exe"
REM
REM =============================================================

set "MODEXPORTER_OUTPUTROOT=C:"

set "PYTHONEXE=C:\Python26\python.exe"
set "BLENDEREXE=C:\Blender\blender.exe"

"%PYTHONEXE%" modexporter_blender_main.py
