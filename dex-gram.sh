#!/bin/bash
# ==========================================
# DEX-GRAM MASTER CONTROL (V2.3 - Resilient)
# ==========================================

cd ~/dex-local

echo "[*] Initializing Dex Neural Architecture..."

# 1. Hard Purge of old instances
fuser -k 8000/tcp > /dev/null 2>&1
pkill -9 -f dex_gatekeeper.py
pkill -9 -f dex_telegram.py
sleep 2

# 2. Memory Check
AVAILABLE_RAM=$(free -m | awk '/^Mem:/{print $4}')
echo "[*] Available RAM: ${AVAILABLE_RAM}MB"

# 3. Start Brain (Using Venv)
echo "[*] Loading Neural Weights into Memory/Swap..."
nohup ./venv/bin/python3 dex_gatekeeper.py > gatekeeper.log 2>&1 &

# BERT loading on swap takes significantly longer
echo "[*] Waiting for Neural initialization (20s)..."
sleep 20

# 4. Status Verification
if pgrep -f "dex_gatekeeper.py" > /dev/null; then
    echo "[+] Gatekeeper stable. Launching Telegram Bridge..."
    nohup ./venv/bin/python3 dex_telegram.py > tg_bridge.log 2>&1 &
else
    echo "[-] CRITICAL: Gatekeeper died. Check 'dmesg' or 'gatekeeper.log'"
    exit 1
fi

sleep 2
if pgrep -f "dex_telegram.py" > /dev/null; then
    echo "[+] DEX-GRAM IS ONLINE."
else
    echo "[-] CRITICAL: Telegram Bridge failed."
    exit 1
fi

