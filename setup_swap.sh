#!/bin/bash
# ==========================================
# DEX SYSTEM STABILITY: SWAP ALLOCATION
# ==========================================

echo "[*] Allocating 4GB Emergency Virtual RAM..."

# 1. Create a 4GB file for swap
sudo fallocate -l 4G /swapfile

# 2. Set the correct permissions
sudo chmod 600 /swapfile

# 3. Setup the swap space
sudo mkswap /swapfile

# 4. Enable the swap
sudo swapon /swapfile

# 5. Make it permanent across reboots
if ! grep -q "/swapfile" /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 6. Adjust swappiness (only use swap when necessary)
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/conf.d/99-swappiness.conf > /dev/null 2>&1 || echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

echo "[+] 4GB Swap Active. Use 'free -h' to verify."

