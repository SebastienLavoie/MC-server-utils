#!/bin/bash

set -o errexit

if [[ -z ${1+x} ]]; then
	echo "Missing server config file name"
	exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/"$1"

echo "Killing server"
send_server_cmd '/save-all'
sleep 5
server_say 'SHUTTING DOWN'
sleep 2
send_server_key 'C-c'
echo "Server killed"
sleep 20

tmux kill-session -t "$SERVER_TMUX"
echo "Session killed"
