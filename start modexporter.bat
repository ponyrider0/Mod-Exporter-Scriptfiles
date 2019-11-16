@echo off

if exist "settings.bat" goto load_settings
echo Creating "settings.bat" file...
copy "settings.template" "settings.bat"

:load_settings
call settings.bat

echo.
echo.
echo =============================================================
echo.
echo  Press any key to start modexporter to Export ESM/ESP files.
echo.
echo =============================================================
pause
echo.

modexporter-2019-Nov-15.exe 2> modexporter_error.log

echo.
echo.
echo =============================================================
echo.
echo  Press any key to start Texture conversion and processing.
echo  Or close window to skip remaining steps.
echo.
echo =============================================================
pause
echo.

"%PYTHONEXE%" modexporter_gimp_main.py

echo.
echo.
echo =============================================================
echo.
echo  Press any key to start Mesh conversion and processing.
echo  Or close window to skip remaining steps.
echo.
echo =============================================================
pause
echo.

"%PYTHONEXE%" modexporter_blender_main.py 2> modexporter_blender_error.log

echo.
echo.
echo =============================================================
echo.
echo  Modexporter conversion and processing complete.
echo  Press any key to close window.
echo.
echo =============================================================
pause
