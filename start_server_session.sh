#!/bin/bash

source /home/slavoie/minecraft/dev/server.conf

echo "Starting server in session $SERVER_TMUX"
tmux new-session -d -s "$SERVER_TMUX"
tmux rename-window -t "$SERVER_TMUX".0 'server'
tmux send-keys -t 'server' "$SERVER_START_SCRIPT" Enter
echo "Starting frontail"
$FRONTAIL_START_SCRIPT
sleep 30