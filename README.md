# iMessage AI Agent

Spec-Driven Development project for a Mac-hosted AI agent that can answer messages, generate SwiftUI projects, and prepare iPhone builds with explicit approval gates.

## Current status

- **Step 1 — Python/OpenAI MVP:** implemented and locally tested without an API key.
- **Step 2 — iMessage bridge:** implemented as a read-only-by-default Mac adapter with an allowlist and explicit send confirmation. Real message access requires Full Disk Access and a live Messages database; real sending is not enabled by default.
- **Step 3 — SwiftUI generation:** implemented as deterministic local project scaffolding.
- **Step 4 — Xcode build/test/sign:** preflight and command wrappers are implemented. This Mac currently has Command Line Tools selected, not full Xcode, and has no signing identities, so a device build cannot be claimed.
- **Step 5 — iPhone installation:** blocked until full Xcode, an Apple ID added to Xcode, a connected/trusted iPhone, and a valid personal-team signing identity are available.

## Quick start

```bash
uv sync
uv run pytest
uv run python -m agent.cli --message "Say hello in one sentence" --offline
```

The online command requires `OPENAI_API_KEY` in the environment. Never commit or paste the key into the repository.

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

## Verification limits

Local tests prove parsing, allowlist enforcement, offline agent behavior, SwiftUI file generation, and Apple preflight reporting. They do **not** prove access to Messages, iMessage delivery, OpenAI API connectivity, Apple signing, or iPhone installation. Those require user-controlled permissions, credentials, and hardware.
