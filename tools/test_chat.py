import os
import sys
import time

sys.path.insert(0, r"D:\tianyi-pet")

from app.net import BridgeClient

replies = []


def on_msg(msg):
    print("MSG", msg, flush=True)
    if msg.get("type") == "reply":
        replies.append(msg)


def on_status(ok, info):
    print("STATUS", ok, info, flush=True)


b = BridgeClient(os.environ.get("TIANYI_WS_URL", ""), "", on_msg, on_status)
b.start()
time.sleep(3.0)
print("sending chat...", flush=True)
b.chat("在吗？一句话回复我")
for _ in range(40):
    time.sleep(1.0)
    if replies:
        break
print("RESULT", replies, flush=True)
