@echo off
setlocal enabledelayedexpansion

echo.
echo Voice Note Processor - Quick Mode
echo =====================================
echo.

REM Check if a file was dropped onto the batch file
if "%~1" neq "" (
    echo File detected: %~1
    echo Processing file automatically...
    echo.
    
    REM Process the dropped file directly
    uv run scripts\process_voice_notes.py "%~1"
    if errorlevel 1 (
        echo.
        echo [ERROR] Processing failed with exit code: !errorlevel!
        echo Please check the error messages above.
        goto :error_exit
    )
    
    echo.
    echo Processing completed successfully!
    goto :success_exit
)

REM If no file was dropped, run interactive mode
echo Instructions:
echo - Paste or type the full path to your voice note file
echo - Or drag and drop a file into this window
echo - Press Enter to process immediately
echo - Type 'quit' to exit
echo.

REM Check if required dependencies are available
echo Checking system requirements...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 'uv' is not installed or not in PATH
    echo Please install uv with: pip install uv
    goto :error_exit
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please ensure your API keys are configured
    echo.
)

REM Run the interactive processor
uv run scripts\process_voice_notes.py --interactive
if errorlevel 1 (
    echo.
    echo [ERROR] Application failed with exit code: !errorlevel!
    echo Please check the error messages above.
    goto :error_exit
)

goto :success_exit

:error_exit
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:success_exit
echo.
echo Press any key to exit...
pause >nul
exit /b 0