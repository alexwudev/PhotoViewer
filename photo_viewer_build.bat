@echo off
REM =========================================================
REM  Photo Viewer - Windows build & install script
REM  Run from this folder:  photo_viewer_build.bat
REM  Requires: Python 3.10+ installed and in PATH
REM =========================================================
setlocal
cd /d "%~dp0"

echo Working directory: %CD%
echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install PyQt6 pyinstaller comtypes
if errorlevel 1 goto :err

echo [2/3] Building PhotoViewer with PyInstaller (onedir, trimmed)...
pyinstaller --noconfirm --onedir --windowed --name PhotoViewer ^
  --exclude-module PyQt6.QtWebEngineCore ^
  --exclude-module PyQt6.QtWebEngineWidgets ^
  --exclude-module PyQt6.QtQml ^
  --exclude-module PyQt6.QtQuick ^
  --exclude-module PyQt6.QtQuick3D ^
  --exclude-module PyQt6.QtMultimedia ^
  --exclude-module PyQt6.QtMultimediaWidgets ^
  --exclude-module PyQt6.QtNetwork ^
  --exclude-module PyQt6.QtSql ^
  --exclude-module PyQt6.QtPdf ^
  --exclude-module PyQt6.QtCharts ^
  --exclude-module PyQt6.Qt3DCore ^
  --exclude-module PyQt6.QtDataVisualization ^
  --exclude-module PyQt6.QtTest ^
  --exclude-module PyQt6.QtBluetooth ^
  --exclude-module PyQt6.QtSerialPort ^
  --exclude-module PyQt6.QtPositioning ^
  --exclude-module PyQt6.QtSensors ^
  --exclude-module PyQt6.QtNfc ^
  --hidden-import comtypes.client ^
  photo_viewer.py
if errorlevel 1 goto :err

echo [3/3] Installing to %LOCALAPPDATA%\PhotoViewer ...
set "TARGET=%LOCALAPPDATA%\PhotoViewer"
if exist "%TARGET%" rmdir /S /Q "%TARGET%"
mkdir "%TARGET%"
xcopy /E /I /Y "dist\PhotoViewer\*" "%TARGET%\" >nul
if errorlevel 1 goto :err

echo.
echo Done! Installed to: %TARGET%\PhotoViewer.exe
echo.
echo Next: double-click photo_viewer_register.reg to register
echo it in the Windows "Open with" list for common image types.
echo.
pause
exit /b 0

:err
echo.
echo [ERROR] Build or install failed.
pause
exit /b 1
