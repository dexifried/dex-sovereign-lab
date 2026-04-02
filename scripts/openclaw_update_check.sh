#!/bin/bash

# Executable Checklist Script for OpenClaw Updates

LOG_DIR="/tmp"
DRY_RUN_LOG="$LOG_DIR/openclaw_update_dryrun.log"
DOCTOR_LOG="$LOG_DIR/openclaw_doctor.log"
BACKUP_DIR="$LOG_DIR/openclaw_backup"

# Utility function to log and check exit codes
check_exit_code() {
    if [ "$1" -ne 0 ]; then
        echo "[ERROR] $2 failed with exit code $1"
        exit $1
    fi
}

# 1. Dry-run for OpenClaw update
echo "Running openclaw update dry-run..."
openclaw update --dry-run > "$DRY_RUN_LOG" 2>&1
check_exit_code $? "openclaw update --dry-run"

# 2. Backup before update
echo "Creating backup directory at $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
openclaw backup "$BACKUP_DIR" > "$BACKUP_DIR/backup.log" 2>&1
check_exit_code $? "openclaw backup"

# 3. Perform the update (requires manual confirmation)
echo "Updating OpenClaw..."
read -p "Confirm update (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "[INFO] Update canceled by user."
    exit 0
fi
openclaw update > "$LOG_DIR/openclaw_update.log" 2>&1
check_exit_code $? "openclaw update"

# 4. Run openclaw doctor to verify system health
echo "Running system health checks..."
openclaw doctor > "$DOCTOR_LOG" 2>&1
check_exit_code $? "openclaw doctor"

# 5. Verify gateway status
echo "Checking OpenClaw gateway status..."
openclaw gateway status --require-rpc
check_exit_code $? "openclaw gateway status"

# 6. Completion message
echo "[SUCCESS] OpenClaw update and checks completed successfully!"