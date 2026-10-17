@echo off
REM Construye GeneradorHorarios.exe en la carpeta dist\ (Windows).
REM Requiere Python 3.11 o más nuevo, instalado con la opción "tcl/tk".
cd /d %~dp0
python -m pip install --upgrade pyinstaller openpyxl
python prueba_ventana.py || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name GeneradorHorarios --paths .. --hidden-import horarios.proyecto --hidden-import horarios.nucleo --hidden-import horarios.motor generador_horarios.py
echo.
echo Listo: dist\GeneradorHorarios.exe
