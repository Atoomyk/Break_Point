@echo off
setlocal
cd /d "%~dp0"

echo Building Break_Point.exe ...
".venv\Scripts\pyinstaller.exe" ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name Break_Point ^
  --hidden-import=pystray._win32 ^
  --hidden-import=customtkinter ^
  main.py

if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo.
echo Done: dist\Break_Point.exe
endlocal
