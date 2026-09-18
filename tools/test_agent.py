import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv-agent" / "Scripts" / "python.exe"
WORKER = ROOT / "tools" / "oi_worker.py"

cfg = {
    "model": "deepseek/deepseek-flash",
    "api_key": "",
    "api_base": "https://api.deepseek.com/v1",
    "context_window": 128000,
    "max_tokens": 4096,
    "auto_run": True,
}

p = subprocess.Popen(
    [str(PY), "-u", str(WORKER), json.dumps(cfg, ensure_ascii=False)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
)

init = p.stdout.readline().strip()
print("INIT:", init)

task = "在 D:/tianyi-pet 目录下创建文件 agent_hello.txt，写入内容 hello tianyi，然后告诉我文件的完整路径。"
p.stdin.write(json.dumps({"type": "chat", "text": task}, ensure_ascii=False) + "\n")
p.stdin.flush()

start = time.time()
while time.time() - start < 240:
    line = p.stdout.readline()
    if not line:
        break
    evt = json.loads(line)
    t = evt.get("type")
    print(f"[{t}] {str(evt.get('text',''))[:180]}")
    if t == "done":
        break

p.stdin.write('{"type":"quit"}\n')
p.stdin.flush()
p.terminate()
