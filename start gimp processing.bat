@echo off
set "PYTHONEXE=C:\Python26\python.exe"
set "GIMPEXE=C:\Program Files\GIMP 2\bin\gimp-console-2.8.exe"

REM "%GIMPEXE%" -idf --batch-interpreter python-fu-eval -b "import sys;sys.path=['.']+sys.path;import modexporter_gimp;modexporter_gimp.run()" -b "pdb.gimp_quit(1)"

"%PYTHONEXE%" modexporter_gimp_main.py
