#!/bin/bash

set -eEuo pipefail

source /home/slavoie/valheim/server.conf
export HOME="/home/slavoie"
docker run --rm --name valheim-server --cap-add=sys_nice --stop-timeout 120 \
       -p 2456-2457:2456-2457/udp  -v "$HOME"/valheim/config:/config  -v "$HOME"/valheim/data:/opt/valheim \
       -e SERVER_NAME="Bueno" -e WORLD_NAME="Bueno" -e SERVER_PASS="$SERVER_PASS" \
       -e SERVER-PUBLIC="true" -e BACKUPS_MAX_AGE="28" ghcr.io/lloesche/valheim-server
