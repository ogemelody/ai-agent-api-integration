# Implementation Plan

## Phase 1 — Foundation

Python package, offline agent path, dependency metadata, and tests.

## Phase 2 — Mac bridge

Read-only SQLite adapter, allowlist, explicit send gate, AppleScript handoff, and permission-aware documentation.

## Phase 3 — SwiftUI generation

Deterministic source generator with no implicit network or signing behavior.

## Phase 4 — Apple verification

Preflight checks and build wrapper. Device installation remains a user-approved follow-up after Xcode and signing are configured.

## Risks and mitigations

- Messages database access may require Full Disk Access: report the permission requirement.
- Command Line Tools are not full Xcode: fail before build.
- Personal signing identities are absent: do not create or infer credentials.
- OpenAI API usage costs credits: use offline tests and a low-cost default model.
