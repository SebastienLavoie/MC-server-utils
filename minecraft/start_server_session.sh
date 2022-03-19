#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/server.conf
SERVER_DIR="$(dirname "$SERVER_START_SCRIPT")"

echo "Starting server in session $SERVER_TMUX"
tmux new-session -d -s "$SERVER_TMUX"
send_server_cmd "cd $SERVER_DIR"
send_server_cmd "$SERVER_START_SCRIPT"
sleep 30
