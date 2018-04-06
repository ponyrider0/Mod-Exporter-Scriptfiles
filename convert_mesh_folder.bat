rem "C:\Program Files (x86)\Blender Foundation\Blender\blender.exe" -p 0 0 1 1 -P "modexporter_blender_convert_one.py" -- %1
set "BLENDEREXE=C:\Program Files (x86)\Blender Foundation\Blender\blender.exe"
set "PYTHONEXE=C:\python26\python.exe"
"%PYTHONEXE%"  convert_mesh_folders_modexporter.py -- "%BLENDEREXE%" %1
pause
