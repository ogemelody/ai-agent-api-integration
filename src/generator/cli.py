import argparse
from pathlib import Path
from .core import generate

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--name", required=True); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    for path in generate(a.name, a.output): print(path)

if __name__ == "__main__": main()
