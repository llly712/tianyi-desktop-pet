"""Run the shell script in tools/cmd.sh on the AstrBot server (base64, no quoting issues).

Output -> tools/rc_out.txt (UTF-8).
"""
import base64
import pathlib
import sys

from remote import run

if __name__ == "__main__":
    script = pathlib.Path(r"D:\tianyi-pet\tools\cmd.sh").read_text(encoding="utf-8")
    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
    text = run(f"echo {b64} | base64 -d | bash")
    pathlib.Path(r"D:\tianyi-pet\tools\rc_out.txt").write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(f"wrote {len(text)} chars\n".encode("utf-8"))
