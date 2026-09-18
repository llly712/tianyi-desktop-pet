"""Run an arbitrary shell command on the AstrBot server: py -3.12 tools/rc.py "<cmd>"

Writes the raw output to tools/rc_out.txt (UTF-8) to avoid console codepage issues.
"""
import sys

from remote import run

if __name__ == "__main__":
    text = run(sys.argv[1])
    with open(r"D:\tianyi-pet\tools\rc_out.txt", "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {len(text)} chars to tools/rc_out.txt")
