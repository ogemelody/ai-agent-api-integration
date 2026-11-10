# iMessage AI Agent

Spec-Driven Development project for a Mac-hosted AI agent that can answer messages, generate SwiftUI projects, and prepare iPhone builds with explicit approval gates.

The Python environment is installed with `uv`. The bridge milestone and Feature 002 conversation path have been verified on macOS. Feature 002 includes explicit activation, sender filtering, offline and live OpenAI Responses API reply generation, pending approval, and an approval-gated Messages handoff. See [`docs/testing-report.md`](docs/testing-report.md) for dated evidence and scope boundaries.


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

### Verified Feature 002 functionality

- Authorized inbound iMessages are detected and unauthorized senders are ignored.
- Offline replies remain approval-gated; a live `gpt-4o-mini` Responses API reply was generated in `openai_responses` mode and queued as `pending_approval`.
- Explicit approval completed the Messages handoff, and the reply appeared in Mac Messages. A read receipt was observed separately as device/application verification.
- Activation watermarks persist across restarts, and polling uses a durable chronological `(message.date, message.ROWID)` cursor so bounded pagination does not lose post-activation rows, including same-timestamp rows.
- The automated suite passes with 36 tests.

## SwiftUI and Apple verification

```bash
uv run python -m generator.cli --name AgentDemo --output generated/AgentDemo
uv run python -m apple.cli preflight
```

The Apple wrapper stops when full Xcode, a simulator, a signing identity, or a connected device is unavailable. It never changes signing settings or installs an app without an explicit command.

## Not yet verified

The following remain incomplete or await end-to-end verification:

- Codex-driven native SwiftUI app creation.
- Xcode build, signing, and installation on a physical iPhone.

## SDD documents

The source of truth is under `specs/001-imessage-agent/`: constitution, requirements/specification, implementation plan, and executable task list.

See [`docs/testing-report.md`](docs/testing-report.md) for the milestone test and verification record.
