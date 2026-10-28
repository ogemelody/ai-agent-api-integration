# iMessage AI Agent

Spec-Driven Development project for a Mac-hosted AI agent that can answer messages, generate SwiftUI projects, and prepare iPhone builds with explicit approval gates.


##  start
![first message arrive.PNG](asset/first%20message%20arrive.PNG)

```bash
uv sync
uv run pytest
uv run python -m agent.cli --message "Say hello in one sentence" --offline
```


## Bridge safety

```bash
cp config/allowlist.example.json config/allowlist.json
uv run python -m bridge.cli --allowlist config/allowlist.json --list-recent 10
```

Sending requires both an allowlisted recipient and explicit confirmation.

## SwiftUI and Apple verification

```bash
uv run python -m generator.cli --name AgentDemo --output generated/AgentDemo
uv run python -m apple.cli preflight
```

The Apple wrapper stops when full Xcode, a simulator, a signing identity, or a connected device is unavailable. It never changes signing settings or installs an app without an explicit command.

## SDD documents

The source of truth is under `specs/001-imessage-agent/`: constitution, requirements/specification, implementation plan, and executable task list.
