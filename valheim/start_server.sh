#!/bin/bash

set -eEuo pipefail

source /home/slavoie/Valheim/server.conf
source /home/slavoie/Valheim/.server.pass

docker run --rm --name valheim-server --cap-add=sys_nice --stop-timeout 120 \
       -p 2456-2457:2456-2457/udp  -v "$SERVER_DIR"/config:/config  -v "$SERVER_DIR"/data:/opt/valheim \
       -e SERVER_NAME="Seb's Server" -e WORLD_NAME="Valhalla" \
       -e SERVER_PASS="$SERVER_PASS" -e BACKUPS_MAX_AGE="28" ghcr.io/lloesche/valheim-server
