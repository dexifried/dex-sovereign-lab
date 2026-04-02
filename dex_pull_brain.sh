#!/bin/bash
# ==========================================
# DEX BRAIN PULL: HF Hub -> Linode Weights
# ==========================================

REPO="Dexifried/dex-router-brain"
LOCAL_DIR=~/dex-local/dex_router_model

echo "[*] Pulling updated weights from $REPO..."

# Use the HF Transfer tool for speed
./venv/bin/huggingface-cli download $REPO --local-dir $LOCAL_DIR --local-dir-use-symlinks False

echo "[+] Neural Weights updated. Run 'bash dex-gram.sh' to reload the Gatekeeper."

