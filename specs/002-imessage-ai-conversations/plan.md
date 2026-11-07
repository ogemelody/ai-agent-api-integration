# Implementation Plan

## Phase 1 — Contract and data model

Define typed inbound-message, candidate-reply, processing-state, approval, and cost-policy models. Document the stable Messages database identity and the fallback identity rules. Keep the existing outbound `recipients` allowlist compatible while adding an explicit inbound sender policy.

## Phase 2 — Safe inbound discovery

Extend the read-only bridge query to return stable IDs, direction metadata, sender identifiers, text, and timestamps. Add inbound-only filtering, sender allowlist checks, self-reply protection, bounded reads, and categorized permission/database errors. Do not add a send side effect to discovery.

## Phase 3 — Persistent idempotent processing

Add a local state store with atomic claim/insert behavior, terminal and retryable statuses, pending approvals, and redacted operator summaries. Ensure restart recovery and concurrent duplicate suppression. The state store must never contain API credentials or unnecessary message history.

## Phase 4 — Agent and cost-controlled response generation

Reuse `Agent.respond` with dependency injection for offline tests and the live client. Add bounded input, output-token, model, per-run, and rate-limit controls. Categorize credential, timeout, quota, rate-limit, and malformed-response failures without logging secrets or full message bodies.

## Phase 5 — Explicit approval handoff

Implement a review/approve/reject workflow that binds approval to one pending source-message ID and one candidate response. Approval calls the existing allowlist and `confirmed=True` send gate exactly once. Rejection, expiry, or cancellation never invokes Messages.

## Phase 6 — Activation and operator safety

Require explicit first-run activation that stores the latest text-message watermark in the durable state store and skips all earlier rows. Load only `OPENAI_API_KEY` from the project-root `.env` when the environment does not already provide it. Keep default pending-queue output limited to redacted IDs and statuses, with private fields available only through explicit opt-in.

## Phase 7 — Verification and documentation

Add unit and integration-style tests with fake bridge, agent, clock, API, and state-store dependencies. Cover authorization, inbound-only behavior, duplicate/concurrency behavior, restart recovery, self-reply prevention, cost limits, credential safety, error handling, approval, and the no-shell invariant. Update user documentation only after implementation and tests are complete.

## Risks and mitigations

- **Messages schema variance:** isolate SQL and direction mapping behind a bridge adapter; fail closed when direction cannot be established.
- **Messages metadata limits:** `ROWID` and `date` provide the activation/deduplication boundary, while `is_from_me` and `handle.id` provide direction and sender identity. These fields do not prove read receipts, delivery, account ownership, or message authenticity; same-Apple-Account loop prevention therefore requires configured local identities in addition to `is_from_me`.
- **Duplicate delivery:** atomically claim source IDs before generation and persist send outcomes before allowing retries.
- **Self-reply loops:** require inbound direction and exclude local identities before every API call; never watch generated outbound content as inbound input.
- **Credential leakage:** rely on the existing client configuration, redact exception details, and keep credentials out of state, arguments, fixtures, and logs.
- **Unexpected API spend:** enforce model, size, token, interval, and per-run limits before the API call.
- **Accidental automation:** keep discovery/generation side-effect free and retain explicit approval plus the existing send confirmation gate.
