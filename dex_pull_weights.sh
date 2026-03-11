#!/bin/bash
echo "=========================================================="
echo "🛰️ DEX MISSION CONTROL: NEURAL RETRIEVAL INITIATED"
echo "=========================================================="

REPO_ID="Dexifried/dex-router-model"
TARGET_DIR="$HOME/dex-local/dex_router_model"

python3 -c "
from huggingface_hub import snapshot_download
import os

repo = '$REPO_ID'
target = os.path.expanduser('$TARGET_DIR')

print(f'[*] Targeting 50GB Model Vault: {repo}')
print(f'[*] Destination: {target}')

try:
    snapshot_download(
        repo_id=repo,
        repo_type='model',
        local_dir=target,
        local_dir_use_symlinks=False
    )
    print('[+] SUCCESS: Neural Weights synchronized to local architecture.')
except Exception as e:
    print(f'[-] FATAL RETRIEVAL ERROR: {e}')
"

echo "=========================================================="
echo "🏁 Retrieval Sequence Complete."
echo "=========================================================="


