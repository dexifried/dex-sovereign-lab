#!/bin/bash
# ==========================================
# AIDER-DEX BRIDGE (V11 - HEADLESS AUTONOMY)
# ==========================================

# 1. 3060 Hardline
export OLLAMA_API_BASE="http://100.65.179.80:11434"

# 2. Neural Shielding (Locked Context)
export AIDER_MAX_CHAT_TOKENS=16384
export AIDER_MAP_TOKENS=4096

# 3. Launch Aider
# - Removed hardcoded --model (dex_agents.py passes this dynamically now)
# - Added --yes-always (Bypasses the "Add file?" prompt for Telegram automation)
aider --api-key ollama=none \
      --edit-format udiff \
      --architect \
      --no-auto-commits \
      --yes-always \
      "$@"


