#!/bin/bash

# Configuration
APP_FILE="app.py"
PID_FILE=".server.pid"
VENV_DIR="venv"
LOG_FILE="server.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Server is already running with PID $PID."
            return
        else
            echo "Found stale PID file. Removing it..."
            rm "$PID_FILE"
        fi
    fi

    echo "Starting Streamlit server..."
    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source ".venv/bin/activate"
    elif [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Run streamlit in the background and detach
    nohup streamlit run "$APP_FILE" > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Save the PID to the file
    echo $PID > "$PID_FILE"
    echo "Server started with PID $PID."
    echo "Logs are being written to $LOG_FILE."
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Server is not running (no PID file found)."
        return
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping server with PID $PID..."
        kill $PID
        rm "$PID_FILE"
        echo "Server stopped."
    else
        echo "Server is not running (stale PID file). Removing it..."
        rm "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Server is running with PID $PID."
        else
            echo "Server is not running, but a stale PID file ($PID_FILE) exists."
        fi
    else
        echo "Server is not running."
    fi
}

if [ $# -eq 0 ]; then
    echo "No command provided. Please choose an action:"
    PS3="Enter a number (1-5): "
    options=("Start Server" "Stop Server" "Check Status" "Restart Server" "Quit")
    select opt in "${options[@]}"
    do
        case $opt in
            "Start Server")
                start
                break
                ;;
            "Stop Server")
                stop
                break
                ;;
            "Check Status")
                status
                break
                ;;
            "Restart Server")
                stop
                sleep 2
                start
                break
                ;;
            "Quit")
                echo "Exiting."
                exit 0
                ;;
            *) echo "Invalid option $REPLY. Please try again." ;;
        esac
    done
else
    case "$1" in
        start)
            start
            ;;
        stop)
            stop
            ;;
        status)
            status
            ;;
        restart)
            stop
            sleep 2
            start
            ;;
        *)
            echo "Usage: $0 {start|stop|status|restart}"
            echo "Or run without arguments for an interactive menu."
            exit 1
            ;;
    esac
fi
