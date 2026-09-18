"""Run an arbitrary command on the AstrBot server over SSH. Usage: ssh.py "<cmd>" """
from __future__ import annotations

import sys

import os

import paramiko

HOST = os.environ.get("TIANYI_SSH_HOST", "")
USER = os.environ.get("TIANYI_SSH_USER", "admin")
PASSWORD = os.environ.get("TIANYI_SSH_PASSWORD", "")


def run(cmd: str, sudo: bool = True) -> str:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, password=PASSWORD, timeout=25)
    full = f"echo {PASSWORD} | sudo -S bash -lc " if sudo else ""
    full += "'" + cmd.replace("'", "'\\''") + "'"
    _in, out, err = cli.exec_command(full)
    data = out.read().decode("utf-8", "replace")
    errdata = err.read().decode("utf-8", "replace")
    cli.close()
    return data + (("\n[stderr]\n" + errdata) if errdata.strip() else "")


if __name__ == "__main__":
    print(run(sys.argv[1]))
