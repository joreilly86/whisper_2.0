@echo off
setlocal enabledelayedexpansion

echo.
echo Voice Note Processor - File Selection
echo =====================================
echo.

REM Set default folder to user's Documents folder
set "DEFAULT_FOLDER=%USERPROFILE%\Documents"

REM Create a PowerShell script to show file dialog
set "PS_SCRIPT=%TEMP%\file_selector.ps1"

REM Write PowerShell script to temp file
echo Add-Type -AssemblyName System.Windows.Forms > "%PS_SCRIPT%"
echo $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog >> "%PS_SCRIPT%"
echo $openFileDialog.InitialDirectory = "%DEFAULT_FOLDER%" >> "%PS_SCRIPT%"
echo $openFileDialog.Filter = "Audio Files (*.mp3;*.wav;*.m4a;*.flac;*.ogg)|*.mp3;*.wav;*.m4a;*.flac;*.ogg|All Files (*.*)|*.*" >> "%PS_SCRIPT%"
echo $openFileDialog.Title = "Select Voice Note to Process" >> "%PS_SCRIPT%"
echo $openFileDialog.Multiselect = $false >> "%PS_SCRIPT%"
echo if ($openFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { >> "%PS_SCRIPT%"
echo     Write-Output $openFileDialog.FileName >> "%PS_SCRIPT%"
echo } else { >> "%PS_SCRIPT%"
echo     Write-Output "CANCELLED" >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"

REM Run PowerShell script to get selected file
echo Opening file selector...
for /f "delims=" %%i in ('powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"') do set "SELECTED_FILE=%%i"

REM Clean up temp file
del "%PS_SCRIPT%"

REM Check if user cancelled
if "!SELECTED_FILE!" == "CANCELLED" (
    echo.
    echo [ERROR] File selection cancelled.
    echo.
    pause
    exit /b 1
)

REM Check if file was selected
if "!SELECTED_FILE!" == "" (
    echo.
    echo [ERROR] No file selected.
    echo.
    pause
    exit /b 1
)

echo.
echo Selected file: !SELECTED_FILE!
echo.
echo Processing voice note...
echo.

REM Process the selected file
uv run scripts\process_voice_notes.py "!SELECTED_FILE!"

echo.
echo [SUCCESS] Processing complete!
echo.
pause