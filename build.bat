@echo off
setlocal
cd /d "%~dp0"

echo [QuickText] Installing build dependencies...
py -3 -m pip install -r requirements-build.txt
if errorlevel 1 (
  echo pip install failed.
  exit /b 1
)

echo [QuickText] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [QuickText] Building onefile windowed EXE...
py -3 -m PyInstaller --noconfirm --clean QuickText.spec
if errorlevel 1 (
  echo PyInstaller failed.
  exit /b 1
)

echo.
echo Build finished.
if exist dist\QuickText.exe (
  dir dist\QuickText.exe
  echo Output: %cd%\dist\QuickText.exe
) else (
  echo ERROR: dist\QuickText.exe was not created.
  exit /b 1
)
endlocal
