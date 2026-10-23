# Feature Specification: iMessage AI Agent

## Goal

Provide a safe Mac-hosted assistant that can answer a message using the OpenAI API, optionally read/send through Messages, generate SwiftUI source, and prepare Apple verification steps.

## Functional requirements

- **FR-001:** Given text, the Python agent returns a response using a configured OpenAI model.
- **FR-002:** The agent supports an offline deterministic mode for local tests.
- **FR-003:** The bridge reads recent text from the local Messages database when macOS permissions allow it.
- **FR-004:** The bridge refuses recipients outside a local allowlist.
- **FR-005:** The bridge refuses sending unless explicit confirmation is supplied.
- **FR-006:** The generator creates a minimal SwiftUI source set from a valid app name.
- **FR-007:** Apple tooling reports whether Xcode, simulators, and signing identities are present before build/install.
- **FR-008:** Build/install actions stop when preflight is incomplete and do not change credentials or signing configuration automatically.

## Non-functional requirements

- No API key, Apple password, or private message content is committed or logged by default.
- Tests run without OpenAI network access, Messages access, Xcode, or an iPhone.
- Unsafe or unavailable operations produce actionable errors.

## Acceptance criteria

1. Offline agent, allowlist, generator, and preflight tests pass locally.
2. A real API call is optional and only occurs when the user supplies `OPENAI_API_KEY`.
3. Real iMessage and iPhone claims require a separately recorded manual verification result.
