# Feature Milestones

This is the SDD implementation ledger. A milestone is complete only when its local evidence is recorded; external capabilities remain blocked until actually observed.

## Milestone 1 — Python/OpenAI agent MVP

**Status:** Complete locally

**Implemented:** Configurable OpenAI client with economical default `gpt-4o-mini`, deterministic offline mode, and a safety prompt against unsupported action claims.

**Evidence:** `/usr/local/bin/python3 -m pytest -q` — 4 passed.

**Not verified:** Live OpenAI API call; intentionally skipped to avoid requiring or exposing credentials.

## Milestone 2 — Secure Mac iMessage bridge

**Status:** Complete locally; external verification blocked

**Implemented:** Read-only SQLite access to `~/Library/Messages/chat.db`, validated recipient allowlist, explicit confirmation gate, actionable permission errors, and Messages AppleScript handoff.

**Evidence:** Bridge allowlist, read-only, send-gate, handoff, and error-reporting tests pass as part of the six-test suite.

**Blocked:** A real read-only check could not open the Messages database under current macOS permissions. No message was sent.

## Milestone 3 — Codex-generated SwiftUI projects

**Status:** Complete locally

**Implemented:** Deterministic generator for an app entry point, `ContentView`, README, and XcodeGen `project.yml`, with Swift identifier validation.

**Evidence:** Generator test passes; `AgentDemo` source and project specification were generated successfully in a temporary output directory.

**Not verified:** XcodeGen is not installed, so no `.xcodeproj` was generated; opening or building in Xcode remains part of Milestone 4.

## Milestone 4 — Xcode build/test/sign gates

**Status:** Complete locally; machine blocked

**Implemented:** Preflight for full Xcode selection, simulator availability, and code-signing identities. Build and test wrappers refuse to start when preflight is incomplete.

**Evidence:** Apple guard tests pass. Current preflight reports Command Line Tools at `/Library/Developer/CommandLineTools`, no simulator utility, zero signing identities, and `ready_for_device_build=False`.

## Milestone 5 — iPhone installation

**Status:** Not started; blocked pending approval and Apple setup

**Required:** Full Xcode, Apple ID/team configured in Xcode, trusted connected iPhone, valid personal signing identity, and explicit approval for build/install.

**Rule:** No device installation or success claim will occur automatically.

## Incremental GitHub delivery

The repository has a configured `origin` remote. The current implementation is ready as one small foundation milestone. Future milestones will use separate focused commits and pushes.
