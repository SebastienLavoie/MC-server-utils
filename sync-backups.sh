#!/bin/bash

set -eo errexit pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/server.conf

BACKUP_LOG_DIR="$SERVER_DIR"/backup-sync-logs
BACKUP_TIME=$(date +%Y%m%dT%H%M%S)
BACKUP_LOG="$BACKUP_LOG_DIR"/"$BACKUP_TIME"-backup-sync.log

mkdir "$BACKUP_LOG_DIR" || true >/dev/null
exec > >(tee -a "$BACKUP_LOG")
exec 2> >(tee -a "$BACKUP_LOG" >&2)

echo "Syncing $FTB_BACKUP_DIR with $REMOTE_BACKUP_DIR"
rclone copy -P  "$FTB_BACKUP_DIR" "$REMOTE_BACKUP_DIR"
