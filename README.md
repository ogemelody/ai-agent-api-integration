# iMessage AI Agent

Spec-Driven Development project for a Mac-hosted AI agent that can answer messages, generate SwiftUI projects, and prepare iPhone builds with explicit approval gates.

The Python environment is installed with `uv`, and the current bridge milestone has been verified on macOS: the Messages database was read after granting Full Disk Access to PyCharm, an allowlisted test message was handed off through Messages, and delivery was observed on a physical iPhone in the Messages app. This does not yet mean that the full AI reply loop is implemented.


## Start
```bash
uv sync
uv run pytest
uv run python -m agent.cli --message "Say hello in one sentence" --offline
```


## Bridge safety

```bash
cp config/allowlist.example.json config/allowlist.json
PYTHONPATH=src uv run python -m bridge.cli --allowlist config/allowlist.json --list-recent 10
```

The bridge reads `~/Library/Messages/chat.db` read-only by default. Sending requires both an allowlisted recipient and explicit confirmation:

```bash
PYTHONPATH=src uv run python -m bridge.cli \
  --allowlist config/allowlist.json \
  --to "<allowlisted recipient>" \
  --text "<test message>" \
  --confirm-send
```

The allowlist file is local configuration and must never be committed. Keep real recipients, message contents, and verification evidence out of public documentation.

### Verified bridge functionality

- `uv sync` completed successfully.
- All 10 automated tests pass: `test_agent.py` (1), `test_apple.py` (4), `test_bridge.py` (4), and `test_generator.py` (1).
- `PYTHONPATH=src` resolves the bridge module when running it directly.
- Full Disk Access for PyCharm allowed a real read-only Messages database check.
- Unauthorized recipients were rejected by the allowlist.
- An allowlisted test message was sent through the bridge and delivery was observed on an actual iPhone in Messages.

### Troubleshooting

- If `bridge` cannot be imported, run the command with `PYTHONPATH=src` as shown above.
- If the Messages database cannot be opened, grant Full Disk Access to the application launching the bridge (for example, PyCharm), then retry the read-only command.
- If sending is rejected, check the local allowlist and the explicit `--confirm-send` flag. Never bypass the allowlist.
- A successful Messages handoff is not proof of delivery; verify the result in Messages on the recipient device.

## SwiftUI and Apple verification

```bash
uv run python -m generator.cli --name AgentDemo --output generated/AgentDemo
uv run python -m apple.cli preflight
```

The Apple wrapper stops when full Xcode, a simulator, a signing identity, or a connected device is unavailable. It never changes signing settings or installs an app without an explicit command.

## Not yet verified

The following remain incomplete or await end-to-end verification:

- Live OpenAI API integration.
- Automatic incoming message listener.
- AI-generated responses delivered through iMessage.
- Duplicate-message and self-reply loop prevention.
- Codex-driven native SwiftUI app creation.
- Xcode build, signing, and installation on a physical iPhone.

## SDD documents

The source of truth is under `specs/001-imessage-agent/`: constitution, requirements/specification, implementation plan, and executable task list.

See [`docs/testing-report.md`](docs/testing-report.md) for the milestone test and verification record.
