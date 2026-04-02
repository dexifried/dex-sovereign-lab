#!/bin/bash
# ==========================================
# DEX HF SYNC: Linode -> ZeroGPU Space
# ==========================================

cd ~/dex-local

# 1. Ensure the dataset is fresh
if [ ! -f "intent_dataset.csv" ]; then
    echo "[-] Error: intent_dataset.csv not found."
    exit 1
fi

# 2. Copy to the Space directory
echo "[*] Syncing dataset to neural-bake directory..."
cp intent_dataset.csv ~/dex-local/dex-neural-bake/

# 3. Push to Hugging Face
cd ~/dex-local/dex-neural-bake
git add intent_dataset.csv
git commit -m "Neural Update: $(date +'%Y-%m-%d %H:%M:%S')"
git push

echo "[+] Dataset is live on HF. Go to your Space and click 'START BAKE'."

