#!/bin/bash

# --- DEX LAB SOVEREIGN CLEANUP ---
# Purpose: Clear zombie bot instances and verify environment state.

echo "===================================================="
echo "          DEX LABORATORY: SYSTEM PURGE             "
echo "===================================================="

# 1. Targeted Process Termination
echo "[*] Identifying and terminating active Dex processes..."

# Kill the gatekeeper (Telegram bot)
pkill -f "dex_gatekeeper.py" && echo "[+] Terminated: dex_gatekeeper.py" || echo "[-] No active gatekeeper found."

# Kill any background miners or loop wrappers
pkill -f "dex_synapse_miner.py" && echo "[+] Terminated: dex_synapse_miner.py" || echo "[-] No active miners found."
pkill -f "bash -c 'for i in" && echo "[+] Terminated: Background loops" || echo "[-] No active loops found."

# 2. Socket Cool-down
# Give the OS a moment to release the network ports
echo "[*] Waiting for network sockets to clear..."
sleep 3

# 3. Final Verification
echo "[*] Performing final process audit..."
STILL_RUNNING=$(pgrep -f "dex_gatekeeper.py")

if [ -z "$STILL_RUNNING" ]; then
    echo "[SUCCESS] Environment is now sterile."
else
    echo "[!] WARNING: Process $STILL_RUNNING is resisting. Escalating to SIGKILL..."
    kill -9 $STILL_RUNNING
    echo "[SUCCESS] Force-purged remaining processes."
fi

# 4. Dataset Integrity Check
echo "----------------------------------------------------"
echo "[*] CURRENT DATASET STATUS:"
if [ -f ~/dex-local/intent_dataset.csv ]; then
    ROW_COUNT=$(wc -l < ~/dex-local/intent_dataset.csv)
    echo "    - Rows: $ROW_COUNT"
    echo "    - Last Entry: $(tail -n 1 ~/dex-local/intent_dataset.csv)"
else
    echo "    - [!] intent_dataset.csv NOT FOUND."
fi
echo "===================================================="

