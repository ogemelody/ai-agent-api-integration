# iMessage Bridge Testing Report

## Verified on 2026-10-28

The Python environment installed successfully with `uv sync`. The automated suite completed with 10 passing tests:

| Test module | Passed |
| --- | ---: |
| `tests/test_agent.py` | 1 |
| `tests/test_apple.py` | 4 |
| `tests/test_bridge.py` | 4 |
| `tests/test_generator.py` | 1 |
| **Total** | **10** |

The bridge was run with `PYTHONPATH=src` to resolve the source package. After Full Disk Access was enabled for PyCharm, the bridge successfully accessed the macOS Messages database in read-only mode. The recipient allowlist rejected an unauthorized recipient, a permitted recipient was configured in local ignored configuration, and a test message was sent through the bridge. Delivery was then observed on an actual iPhone using the Messages application.

## Scope boundaries for the 2026-10-28 bridge-only check

The 2026-10-28 bridge-only check did not claim live OpenAI API usage, an automatic incoming message listener, AI-generated iMessage replies, duplicate-message or self-reply loop prevention, Codex-driven native SwiftUI app creation, or Xcode build/sign/install on a physical iPhone. Feature 002 results are recorded separately below.

No private message contents, recipient identifiers, verification codes, Apple credentials, local allowlist contents, or private screenshots are included in this repository report.

## Feature 002 live integration verification — 2026-11-10

The Feature 002 conversation path was exercised on a configured Mac without recording private message data. The following behaviors were observed:

- An authorized inbound iMessage was detected.
- The inbound sender allowlist was enforced; an unauthorized message was ignored without an agent request.
- An offline reply was generated and remained approval-gated.
- A live OpenAI Responses API reply was generated with `gpt-4o-mini` in `openai_responses` mode.
- The generated response was stored as `pending_approval`.
- Explicit approval was performed, and the approved reply appeared in Mac Messages.
- A read receipt was observed in Messages as an independent application/device verification.
- The automated suite completed with 36 passing pytest tests.

The Messages handoff and device verification are separate claims: a successful approval-gated handoff confirms that the bridge completed its permitted Messages operation; it does not independently prove device delivery. The observed read receipt is recorded separately as the device/application observation.

Feature 002 also preserves its activation boundary in the state database across restarts. Polling now uses a separate durable `(message.date, message.ROWID)` cursor in chronological order. The previous oldest-row query repeatedly returned historical rows, so post-activation messages could be missed once the polling limit was reached. Regression coverage now includes old history exclusion, new inbound rows, bounded pagination, same-timestamp rows, repeated polls, and restart recovery without resetting or reactivating the existing state.

No phone numbers, Apple IDs, private message text, screenshots, API keys, `.env` contents, or SQLite database contents are included here.
