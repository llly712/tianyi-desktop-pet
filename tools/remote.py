"""Run a shell command on the AstrBot server over SSH (for protocol inspection)."""
from __future__ import annotations

import sys

import os

import paramiko

HOST = os.environ.get("TIANYI_SSH_HOST", "")
USER = os.environ.get("TIANYI_SSH_USER", "admin")
PASSWORD = os.environ.get("TIANYI_SSH_PASSWORD", "")

PLUGIN = "/www/dk_project/dk_app/astrbot/astrbot_MHCM/data/plugins/astrbot_plugin_pet_bridge/main.py"


def run(cmd: str) -> str:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, password=PASSWORD, timeout=20)
    full = f"echo {PASSWORD} | sudo -S bash -lc {shell_quote(cmd)}"
    _in, out, err = cli.exec_command(full)
    data = out.read().decode("utf-8", "replace")
    errdata = err.read().decode("utf-8", "replace")
    cli.close()
    return data + ("\n[stderr]\n" + errdata if errdata.strip() else "")


def shell_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "_send_agent_to_pet"
    print(run(f"grep -n -E {shell_quote(pattern)} {PLUGIN}"))
