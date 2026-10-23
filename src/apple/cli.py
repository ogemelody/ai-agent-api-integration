import argparse
from pathlib import Path
from .core import build, preflight

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("command", choices=["preflight", "build"]); p.add_argument("--project", type=Path); a = p.parse_args()
    if a.command == "preflight":
        state = preflight(); print(state); print("ready_for_device_build=" + str(state.ready_for_device_build))
    else:
        if not a.project: p.error("--project is required for build")
        build(a.project)

if __name__ == "__main__": main()
