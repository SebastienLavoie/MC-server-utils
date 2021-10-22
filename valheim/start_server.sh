docker run -d --name valheim-server --cap-add=sys_nice --stop-timeout 120 \
       -p 2456-2457:2456-2457/udp  -v "$HOME"/valheim/config:/config  -v "$HOME"/valheim/data:/opt/valheim \
       -e SERVER_NAME="Bueno" -e WORLD_NAME="Bueno" -e SERVER_PASS="RVmdCQjBAsAa9sDJ" \
       -e SERVER-PUBLIC=true ghcr.io/lloesche/valheim-server
