import argparse
from .core import Agent, AgentConfig

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI agent MVP")
    parser.add_argument("--message", required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    print(Agent(AgentConfig(model=args.model)).respond(args.message, offline=args.offline))

if __name__ == "__main__":
    main()
