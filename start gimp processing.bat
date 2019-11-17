@echo off

if exist "settings.bat" goto load_settings
echo Creating "settings.bat" file...
copy "settings.template" "settings.bat"

:load_settings
call settings.bat

"%PYTHONEXE%" modexporter_gimp_main.py

pause