import argparse
from pathlib import Path
from .core import Allowlist, MessagesBridge

def main() -> None:
    p = argparse.ArgumentParser(description="Read or explicitly send through Messages")
    p.add_argument("--allowlist", type=Path, required=True); p.add_argument("--database", type=Path)
    p.add_argument("--list-recent", type=int); p.add_argument("--to"); p.add_argument("--text")
    p.add_argument("--confirm-send", action="store_true"); a = p.parse_args()
    try:
        bridge = MessagesBridge(Allowlist.load(a.allowlist), a.database)
        if a.list_recent is not None:
            for item in bridge.recent_messages(a.list_recent): print(f"{item['sender']}: {item['text']}")
        elif a.to and a.text:
            bridge.send(a.to, a.text, confirmed=a.confirm_send); print("Message handoff completed; verify delivery separately")
        else: p.error("choose --list-recent or both --to and --text")
    except (PermissionError, RuntimeError, ValueError) as exc:
        p.error(str(exc))

if __name__ == "__main__": main()
