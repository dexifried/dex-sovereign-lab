#!/bin/bash
# Dex Sovereign: Remote Linker & Force Synchronizer

# 1. Enter the directory
cd ~/dex-local

# 2. Add the remote (REPLACE THESE WITH YOUR ACTUAL SPACE DETAILS)
# Example: https://huggingface.co/spaces/Dexifried/dex-neural-lab
REMOTE_URL="https://huggingface.co/spaces/Dexifried/dex-neural-bake"

echo "[*] Attempting to link to $REMOTE_URL..."

# Remove 'origin' if it exists to avoid conflicts
git remote remove origin 2>/dev/null

# Add the correct origin
git remote add origin $REMOTE_URL

# 3. Final Push Attempt
echo "[*] Pushing DNA and Logic to the Hub..."
git push origin main --force

echo "=========================================================="
echo "📡 If you see 'Everything up-to-date' or a progress bar," 
echo "   your Space is now synchronized."
echo "=========================================================="

