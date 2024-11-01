#!/bin/bash

if [[ -z ${1+x} ]];then
	echo "Missing server config file name"
	exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/"$1"
SERVER_DIR="$(dirname "$SERVER_START_SCRIPT")"

echo "Starting server in session $SERVER_TMUX"
tmux new-session -d -s "$SERVER_TMUX"
sleep 2
send_server_cmd "cd $SERVER_DIR"
send_server_cmd "$SERVER_START_SCRIPT"
sleep 30
