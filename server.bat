@echo off
REM WiFi File Transfer — Quick launcher for Windows
REM Usage: Double-click this file, or run from Command Prompt
REM        server.bat start | stop | restart | status | install

title WiFi File Transfer

cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo  ====================================
    echo    WiFi File Transfer
    echo  ====================================
    echo.
    echo    1. Start Server
    echo    2. Stop Server
    echo    3. Check Status
    echo    4. Restart Server
    echo    5. Install Dependencies
    echo    6. Quit
    echo.
    set /p choice="  Enter your choice (1-6): "
    if "%choice%"=="1" goto start_server
    if "%choice%"=="2" goto stop_server
    if "%choice%"=="3" goto check_status
    if "%choice%"=="4" goto restart_server
    if "%choice%"=="5" goto install_deps
    if "%choice%"=="6" goto quit
    echo  Invalid choice.
    pause
    goto :eof
)

if /i "%~1"=="start" goto start_server
if /i "%~1"=="stop" goto stop_server
if /i "%~1"=="status" goto check_status
if /i "%~1"=="restart" goto restart_server
if /i "%~1"=="install" goto install_deps
echo Usage: %~nx0 {start^|stop^|status^|restart^|install}
goto :eof

:start_server
    REM Check if already running
    if exist .server.pid (
        set /p PID=<.server.pid
        tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
        if not errorlevel 1 (
            echo  Server is already running ^(PID %PID%^).
            goto end_pause
        ) else (
            echo  Found stale PID file, removing...
            del .server.pid
        )
    )

    REM Find Python in venv
    set PYTHON=
    if exist .venv\Scripts\python.exe (
        set PYTHON=.venv\Scripts\python.exe
    ) else if exist venv\Scripts\python.exe (
        set PYTHON=venv\Scripts\python.exe
    ) else (
        echo  Creating virtual environment...
        python -m venv .venv
        if errorlevel 1 (
            echo  ERROR: Failed to create venv. Is Python installed?
            echo  Download Python from https://www.python.org/downloads/
            goto end_pause
        )
        set PYTHON=.venv\Scripts\python.exe
        echo  Installing dependencies...
        .venv\Scripts\python.exe -m pip install -r requirements.txt -q
    )

    REM Check if streamlit is installed
    %PYTHON% -c "import streamlit" 2>nul
    if errorlevel 1 (
        echo  Installing dependencies...
        %PYTHON% -m pip install -r requirements.txt -q
    )

    echo  Starting WiFi File Transfer server...
    start /b "" %PYTHON% -m streamlit run app.py > server.log 2>&1
    
    REM Get the PID of the last started process
    for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do set PID=%%a
    echo %PID% > .server.pid
    echo  Server started.
    echo  Logs: server.log

    timeout /t 3 /nobreak >nul
    if exist server.log (
        findstr /C:"Local URL" server.log
        findstr /C:"Network URL" server.log
    )
    goto end_pause

:stop_server
    if not exist .server.pid (
        echo  Server is not running.
        goto end_pause
    )
    set /p PID=<.server.pid
    echo  Stopping server ^(PID %PID%^)...
    taskkill /F /PID %PID% >nul 2>&1
    del .server.pid
    echo  Server stopped.
    goto end_pause

:check_status
    if not exist .server.pid (
        echo  Server is not running.
        goto end_pause
    )
    set /p PID=<.server.pid
    tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
    if not errorlevel 1 (
        echo  Server is running ^(PID %PID%^).
        if exist server.log (
            findstr /C:"Local URL" server.log
            findstr /C:"Network URL" server.log
        )
    ) else (
        echo  Server is not running ^(stale PID file^).
        del .server.pid
    )
    goto end_pause

:restart_server
    call :stop_server
    timeout /t 2 /nobreak >nul
    call :start_server
    goto :eof

:install_deps
    if not exist .venv\Scripts\python.exe (
        echo  Creating virtual environment...
        python -m venv .venv
    )
    echo  Installing dependencies...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo  Done.
    goto end_pause

:quit
    exit /b 0

:end_pause
    if "%~1"=="" pause
    goto :eof
