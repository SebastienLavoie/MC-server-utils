#!/bin/bash

set -o errexit

source /home/slavoie/minecraft/dev/server.conf

echo "Killing server - giving 30s warning"
server_say 'SHUTTING DOWN SERVER IN 30s'
send_server_cmd '/save-all'
sleep 20
server_say 'SHUTTING DOWN SERVER IN 10s'
sleep 10
server_say 'SHUTTING DOWN'
sleep 2
send_server_key 'C-c'
echo "Server killed"
sleep 30

tmux kill-session -t "$SERVER_TMUX"
echo "Session killed"
docker kill mc-frontail
