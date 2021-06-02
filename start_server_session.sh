#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR"/server.conf

echo "Starting server in session $SERVER_TMUX"
tmux new-session -d -s "$SERVER_TMUX"
tmux rename-window -t "$SERVER_TMUX".0 'server'
tmux send-keys -t 'server' "$SERVER_START_SCRIPT" Enter
echo "Starting frontail"
$FRONTAIL_START_SCRIPT
sleep 30