import subprocess
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import time

def get_project_name(pid):
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")

        # Customize this path to YOUR dev folder
        if "/projects/" in cwd:
            return cwd.split("/projects/")[-1].split("/")[0]

        return "-"
    except:
        return "-"

def live_view(filter_term=None):
    try:
        with Live(refresh_per_second=1) as live:
            while True:
                ports = get_ports()
                table = build_table(ports, filter_term)

                live.update(Panel(table))
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Exiting PortWatch[/yellow]")

def get_ports():
    result = subprocess.run(
        ["ss", "-tulnp"],
        capture_output=True,
        text=True
    )

    lines = result.stdout.split("\n")
    ports = {}

    for line in lines[1:]:
        if "LISTEN" not in line:
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        local_address = parts[4]
        process_info = parts[-1] if len(parts) > 6 else ""

        port = local_address.split(":")[-1]

        pid = "?"
        if "pid=" in process_info:
            pid = process_info.split("pid=")[1].split(",")[0]

        process = "unknown"
        if '"' in process_info:
            process = process_info.split('"')[1]

        if port not in ports:
            ports[port] = (process, pid)

    return ports


console = Console()


def display(ports, filter_term=None):
    table = Table(title="🚀 PortWatch")

    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Process", style="magenta")
    table.add_column("PID", style="yellow")
    table.add_column("Project", style="green")

    for port in sorted(ports, key=lambda x: int(x)):
        process, pid = ports[port]

        if filter_term and filter_term.lower() not in process.lower():
            continue

        project = "-"
        if pid != "?":
            project = get_project_name(pid)

        table.add_row(port, process, pid, project)

    console.print(table)


def kill_port(port):
    ports = get_ports()

    if port not in ports:
        print(f"❌ Port {port} not found")
        return

    process, pid = ports[port]

    if pid == "?":
        print(f"⚠️ Cannot determine PID for port {port}")
        return

    try:
        os.kill(int(pid), 9)
        print(f"🔥 Killed {process} (PID {pid}) on port {port}")
    except PermissionError:
        print("❌ Permission denied. Try with sudo.")
    except ProcessLookupError:
        print("❌ Process not found.")

def build_table(ports, filter_term=None):
    table = Table(title="🚀 PortWatch (Live)")

    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Process", style="magenta")
    table.add_column("PID", style="yellow")
    table.add_column("Project", style="green")

    for port in sorted(ports, key=lambda x: int(x)):
        process, pid = ports[port]

        if filter_term and filter_term.lower() not in process.lower():
            continue

        project = "-"
        if pid != "?":
            project = get_project_name(pid)

        table.add_row(port, process, pid, project)

    return table


def main():
    ports = get_ports()

    if len(sys.argv) == 1:
        display(ports)

    elif sys.argv[1] == "kill":
        if len(sys.argv) < 3:
            print("Usage: portwatch kill <port>")
        else:
            kill_port(sys.argv[2])

    elif sys.argv[1] == "live":
        live_view()

    else:
        filter_term = sys.argv[1]
        display(ports, filter_term)

