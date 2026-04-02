#!/bin/bash
# ==========================================
# DEX SOVEREIGN LAB MANAGER (V1.0)
# ==========================================

# Colors for the terminal
G='\033[0;32m'
B='\033[0;34m'
A='\033[0;33m'
NC='\033[0m'

cd ~/dex-local

show_status() {
    echo -e "${B}[*] LAB STATUS AUDIT${NC}"
    echo -e "RAM: $(free -m | awk '/^Mem:/{print $3}')MB / $(free -m | awk '/^Mem:/{print $2}')MB"
    pgrep -f "dex_gatekeeper.py" > /dev/null && echo -e "Gatekeeper: ${G}ONLINE${NC}" || echo -e "Gatekeeper: ${A}OFFLINE${NC}"
    pgrep -f "dex_telegram.py" > /dev/null && echo -e "Telegram:   ${G}ONLINE${NC}" || echo -e "Telegram:   ${A}OFFLINE${NC}"
}

case "$1" in
    "mine")
        echo -e "${B}[*] Tapping Omniscience Vault via DeepSeek-V3.2...${NC}"
        ./venv/bin/python3 dex_synapse_miner.py
        echo -e "${G}[+] Mining Complete.${NC}"
        ;;
    "sync")
        echo -e "${B}[*] Syncing Dataset to ZeroGPU Space...${NC}"
        cp intent_dataset.csv ~/dex-local/dex-neural-bake/
        cd ~/dex-local/dex-neural-bake
        git add intent_dataset.csv
        git commit -m "Neural Update: $(date +'%Y-%m-%d %H:%M:%S')"
        git push
        echo -e "${G}[+] Dataset is live. Go to HF and click 'START BAKE'.${NC}"
        ;;
    "pull")
        echo -e "${B}[*] Pulling Neural Weights from HF Hub...${NC}"
        hf download Dexifried/dex-router-brain --local-dir ~/dex-local/dex_router_model
        echo -e "${G}[+] Weights updated.${NC}"
        ;;
    "reboot")
        echo -e "${B}[*] Restarting Neural Architecture...${NC}"
        bash dex-gram.sh
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Usage: ./dex.sh {mine|sync|pull|reboot|status}"
        exit 1
        ;;
esac

