import argparse
from pathlib import Path
from .core import build, device_preflight, preflight, test

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("command", choices=["preflight", "build", "test", "device-preflight"]); p.add_argument("--project", type=Path); a = p.parse_args()
    if a.command == "preflight":
        state = preflight(); print(state); print("ready_for_device_build=" + str(state.ready_for_device_build))
    elif a.command == "device-preflight":
        state = device_preflight(); print(state); print("ready_for_install=" + str(state.ready_for_install))
    else:
        if not a.project: p.error("--project is required for build")
        (test if a.command == "test" else build)(a.project)

if __name__ == "__main__": main()
