#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
soure "$SCRIPT_DIR"/server.conf

set -o errexit

DATE_STR=$(date +%Y%m%dT%H%M%S)
LOCAL_EXPIRY_DAYS=4
CLOUD_EXPIRY_DAYS=14

function delete_files_older_than () {
    expiry=$1
    dir=$2
    echo "Deleting backups older than $expiry days in $dir"
    NUM_DELETIONS=$(find "$dir" -atime +$LOCAL_EXPIRY_DAYS -type f -name "$SERVER_NAME"-'*.tar.gz' | wc -l) 
    if [ "$NUM_DELETIONS" != 0 ]
    then
        echo "Following files have been deleted:"
        find "$dir" -atime +$LOCAL_EXPIRY_DAYS -type f -name "$SERVER_NAME"-'*.tar.gz' -delete -print
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
tar cf "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz "$SERVER_DIR"
echo "Copying to cloud..."
rclone copy -P "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz "$REMOTE_BACKUP_DIR"
server_say 'Backup Done'
echo "Backup Done"
delete_files_older_than "$LOCAL_EXPIRY_DAYS" "$BACKUP_DIR"
delete_files_older_than "$CLOUD_EXPIRY_DAYS" "$CLOUD_BACKUP_DIR"
echo "---------------------------------------------------------------------"
