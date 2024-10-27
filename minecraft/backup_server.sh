#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/server.conf

set -eo errexit pipefail

DATE_STR=$(date +%Y%m%dT%H%M%S)
LOCAL_EXPIRY_DAYS=7
CLOUD_EXPIRY_DAYS=14
MAX_DIR_SIZE=536870912000  # 500GiB
dry_run=false

msg() {
  echo >&2 -e "${1-}"
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "$msg"
  exit "$code"
}

parse_params() {
  while :; do
    case "${1-}" in
    -v | --verbose) set -x ;;
    -d | --dry-run) dry_run=true ;;
    -?*) die "Unknown option: $1" ;;
    *) break ;;
    esac
    shift
  done
  return 0
}

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

function dir_size() {
  dir=$1
  size=$(du -sb "$dir" | cut -f1)
  echo "Current directory size is $(du -sh "$dir")"
}

parse_params "$@"

echo "---------------------------------------------------------------------"
echo "Starting backup for $DATE_STR"
if [ "$dry_run" = "true" ]; then
  echo "Doing dry run"
  server_say "Doing dry run"
fi
server_say 'Starting Backup'
sleep 1
send_server_cmd '/save-all'
sleep 5

start_time=$(date +%s)
if [ -e /tmp/mc-backup ]; then
    rm -rf /tmp/mc-backup
fi
mkdir /tmp/mc-backup
echo "Copying to /tmp ..."
cp -a "$SERVER_DIR"/world /tmp/mc-backup/
if [ "$dry_run" = "false" ]; then
  echo "Compressing..."
  tar cf "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz /tmp/mc-backup/world
fi
rm -rf /tmp/mc-backup
stop_time=$(date +%s)
exec_time=$(("$stop_time" - "$start_time"))
disk_usage_pcent=$(df --output=pcent "$BACKUP_DIR" | tail -n 1 | tr -d ' ')
server_say "Backup Done In ${exec_time}s. Backup disk is ${disk_usage_pcent} full"
echo "Backup Done In ${exec_time}s. Backup disk is ${disk_usage_pcent} full"

if [ ! -z ${CLOUD_BACKUP_DIR+x} ]; then
	server_say "Uploading to cloud..."
	echo "Uploading to cloud..."
	start_time=$(date +%s)
	if [ "$dry_run" = "false" ]; then
	  rclone copy -P "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz "$REMOTE_BACKUP_DIR"
	fi
	stop_time=$(date +%s)
	exec_time=$(("$stop_time" - "$start_time"))
	file_size=$(du -h "$BACKUP_DIR"/"$SERVER_NAME"-"$DATE_STR".tar.gz | cut -f1)
	server_say "Upload Complete In ${exec_time}s. File size ${file_size}"
	echo "Upload Complete In ${exec_time}s. File size ${file_size}"
fi

if [ "$dry_run" = "false" ]; then
  delete_files_older_than "$LOCAL_EXPIRY_DAYS" "$BACKUP_DIR"
  if [ ! -z ${CLOUD_BACKUP_DIR+x} ]; then
    delete_files_older_than "$CLOUD_EXPIRY_DAYS" "$CLOUD_BACKUP_DIR"
  fi
fi
echo "---------------------------------------------------------------------"
