#!/bin/bash
# Dex Sovereign Grounding Scan
# This script dumps all core logic for re-alignment.

echo "--- START OF DEX GROUNDING DUMP ---"

echo "### FILE: DEX_MANIFEST.md"
cat ~/dex-local/DEX_MANIFEST.md
echo "---"

echo "### FILE: dex_config.json"
cat ~/dex-local/dex_config.json
echo "---"

echo "### FILE: dex_gatekeeper.py"
cat ~/dex-local/dex_gatekeeper.py
echo "---"

echo "### FILE: dex_agents.py"
cat ~/dex-local/dex_agents.py
echo "---"

echo "### FILE: dex_telegram.py"
cat ~/dex-local/dex_telegram.py
echo "---"

echo "### FILE: dex_memory.py"
cat ~/dex-local/dex_memory.py
echo "---"

echo "### FILE: aider-dex.sh"
cat ~/dex-local/aider-dex.sh
echo "---"

echo "### DATA: intent_dataset.csv (Head)"
head -n 30 ~/dex-local/intent_dataset.csv
echo "---"

echo "### DATA: surgical_ledger.md (Tail)"
tail -n 50 ~/dex-local/surgical_ledger.md
echo "---"

echo "--- END OF DEX GROUNDING DUMP ---"


