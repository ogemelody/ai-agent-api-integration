# Feature Milestones

This is the SDD implementation ledger. A milestone is complete only when its local evidence is recorded; external capabilities remain blocked until actually observed.

## Milestone 1 — Python/OpenAI agent MVP

**Status:** Complete locally

**Implemented:** Configurable OpenAI client with economical default `gpt-4o-mini`, deterministic offline mode, and a safety prompt against unsupported action claims.

**Evidence:** `/usr/local/bin/python3 -m pytest -q` — 4 passed.

**Not verified:** Live OpenAI API call; intentionally skipped to avoid requiring or exposing credentials.

## Milestone 2 — Secure Mac iMessage bridge

**Status:** Verified bridge read/send milestone

**Implemented:** Read-only SQLite access to `~/Library/Messages/chat.db`, validated recipient allowlist, explicit confirmation gate, actionable permission errors, and Messages AppleScript handoff.

**Evidence:** `uv sync` completed; the full suite passes with 10 tests (bridge: 4); `PYTHONPATH=src` fixed direct module discovery; Full Disk Access for PyCharm enabled a real read-only Messages database check; an unauthorized recipient was blocked; an allowlisted recipient was configured locally; and a test message was handed off through Messages and observed delivered on a physical iPhone.

**Not implemented or not end-to-end verified:** automatic incoming message listening, AI-generated responses delivered through iMessage, and duplicate-message/self-reply loop prevention.

## Milestone 3 — Codex-generated SwiftUI projects

**Status:** Complete locally

**Implemented:** Deterministic generator for an app entry point, `ContentView`, README, and XcodeGen `project.yml`, with Swift identifier validation.

**Evidence:** Generator test passes; `AgentDemo` source and project specification were generated successfully in a temporary output directory.

**Not verified:** Codex-driven native SwiftUI app creation and XcodeGen/project generation remain unverified; opening or building in Xcode remains part of Milestone 4.

## Milestone 4 — Xcode build/test/sign gates

**Status:** Complete locally; machine blocked

**Implemented:** Preflight for full Xcode selection, simulator availability, and code-signing identities. Build and test wrappers refuse to start when preflight is incomplete.

**Evidence:** Apple guard tests pass. Current preflight reports Command Line Tools at `/Library/Developer/CommandLineTools`, no simulator utility, zero signing identities, and `ready_for_device_build=False`.

## Milestone 5 — iPhone installation

**Status:** Preflight guard implemented; installation blocked pending approval and Apple setup

**Implemented:** Non-installing device preflight that requires full Xcode, signing readiness, and a detected physical iPhone.

**Required:** Full Xcode, Apple ID/team configured in Xcode, trusted connected iPhone, valid personal signing identity, and explicit approval for build/install.

**Evidence:** Device preflight guard tests pass. No device installation or success claim will occur automatically.

**Remaining:** Xcode build, signing, and installation on a physical iPhone.

## Incremental GitHub delivery

The repository has a configured `origin` remote. This verified bridge milestone is recorded as a focused documentation update. Future implementation milestones will use separate focused commits and pushes.
