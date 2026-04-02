#!/bin/bash

# --- 🛰️ DEX SOVEREIGN LAB VOCAL BRIDGE ---
# Manages the MCP Server and Ngrok tunnel in the background.

LOG_DIR=~/dex-local/logs
mkdir -p $LOG_DIR

MCP_LOG=$LOG_DIR/mcp.log
NGROK_LOG=$LOG_DIR/ngrok.log
PID_FILE=$LOG_DIR/bridge.pid

start_bridge() {
    echo "[*] Killing existing bridge processes..."
    pkill -f dex_mcp_server.py
    pkill -f ngrok
    sleep 2

    echo "[*] Launching Dex MCP Server (Port 8001)..."
    python3 ~/dex-local/dex_mcp_server.py > $MCP_LOG 2>&1 &
    MCP_PID=$!

    echo "[*] Launching Ngrok Tunnel..."
    ngrok http 8001 --log=stdout > $NGROK_LOG 2>&1 &
    NGROK_PID=$!

    echo "$MCP_PID $NGROK_PID" > $PID_FILE

    echo "[*] Waiting for tunnel URL (Retry loop)..."
    PUBLIC_URL=""
    for i in {1..12}; do
        # Fixed Regex: Captures both .app and .dev domains
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.[a-z]*' | head -n 1)
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
        echo "[...] Waiting for tunnel heartbeat..."
        sleep 1
    done

    if [ -z "$PUBLIC_URL" ]; then
        echo "[-] ERROR: Failed to extract URL. Check: cat $NGROK_LOG"
        exit 1
    fi

    echo "=================================================="
    echo "🚀 DEX VOCAL BRIDGE ACTIVE"
    echo "🔗 ELEVENLABS URL: $PUBLIC_URL/sse"
    echo "=================================================="
    echo "[!] Use 'tail -f $MCP_LOG' to monitor activity."
}

stop_bridge() {
    echo "[*] Shutting down bridge..."
    if [ -f $PID_FILE ]; then
        read MCP_PID NGROK_PID < $PID_FILE
        kill $MCP_PID $NGROK_PID 2>/dev/null
        rm $PID_FILE
    fi
    pkill -f dex_mcp_server.py
    pkill -f ngrok
    echo "[+] Bridge Offline."
}

case "$1" in
    start) start_bridge ;;
    stop) stop_bridge ;;
    restart) stop_bridge && sleep 1 && start_bridge ;;
    status)
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.[a-z]*' | head -n 1)
        [ -n "$PUBLIC_URL" ] && echo "[+] Online: $PUBLIC_URL/sse" || echo "[-] Offline"
        ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac

