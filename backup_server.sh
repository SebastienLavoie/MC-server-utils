#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/server.conf

set -o errexit

DATE_STR=$(date +%Y%m%dT%H%M%S)
LOCAL_EXPIRY_DAYS=4
CLOUD_EXPIRY_DAYS=14

function delete_files_older_than() {
  expiry=$1
  dir=$2
  echo "Deleting backups older than $expiry days in $dir"
  NUM_DELETIONS=$(find "$dir" -atime +"$expiry" -type f -name "$SERVER_NAME"-'*.tar.gz' | wc -l)
  if [ "$NUM_DELETIONS" != 0 ]; then
    echo "Following files have been deleted:"
    find "$dir" -atime +"$expiry" -type f -name "$SERVER_NAME"-'*.tar.gz' -delete -print
  else
    echo "No files to delete"
  fi
}

echo "---------------------------------------------------------------------"
echo "Starting backup for $DATE_STR"
server_say 'Starting Backup'
sleep 1
send_server_cmd '/save-all'
sleep 5

start_time=$(date +%s)
mkdir /tmp/mc-backup
cp -a "$SERVER_DIR" /tmp/mc-backup/
tar cf "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz /tmp/mc-backup/"$(basename "$SERVER_DIR")"
rm -rf /tmp/mc-backup
stop_time=$(date +%s)
exec_time=$(("$stop_time" - "$start_time"))
server_say "Backup Done In ${exec_time}s. Uploading To Cloud..."
echo "Backup Done In ${exec_time}s. Uploading To Cloud..."

start_time=$(date +%s)
rclone copy -P "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz "$REMOTE_BACKUP_DIR"
stop_time=$(date +%s)
exec_time=$(("$stop_time" - "$start_time"))
file_size=$(du -h "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz | cut -f1)
server_say "Upload Complete In {$exec_time}s. File size {$file_size}"
echo "Upload Complete In {$exec_time}s. File size ${file_size}"
delete_files_older_than "$LOCAL_EXPIRY_DAYS" "$BACKUP_DIR"
delete_files_older_than "$CLOUD_EXPIRY_DAYS" "$CLOUD_BACKUP_DIR"
echo "---------------------------------------------------------------------"
