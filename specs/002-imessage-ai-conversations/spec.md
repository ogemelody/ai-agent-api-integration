# Feature Specification: Automatic iMessage AI Conversations

## Goal

Extend the existing Python agent and macOS Messages bridge so that authorized incoming iMessages can be discovered, filtered, passed to the configured OpenAI client, and prepared as replies. Sending remains an explicit, user-approved action; an incoming message must never cause an automatic outbound message or shell command.

## Scope and safety boundary

Feature 002 automates detection, classification, response generation, and approval preparation. It does not authorize unattended sending. The existing `MessagesBridge.send(..., confirmed=True)` confirmation gate remains mandatory for every outbound message.

The feature must reuse the existing `bridge.core.MessagesBridge` and `agent.core.Agent` abstractions or compatible extensions. Message text is data only: it must never be interpreted as a command, passed to a shell, or used to construct an executable command.

## Actors and states

- **Watcher:** Reads the local Messages database in read-only mode and identifies newly eligible inbound messages.
- **Agent:** Generates a candidate response through the configured OpenAI client or deterministic offline mode.
- **Approver:** Reviews a candidate and explicitly approves or rejects the outbound handoff.
- **Processing record:** Persisted state keyed by a stable message identifier, with statuses such as `discovered`, `ignored`, `pending_approval`, `approved`, `sent`, and `failed`.

The state machine must be monotonic for a message during normal operation: a message is not sent twice, and a failed or pending item can be retried only through an explicit, auditable action.

## Functional requirements

- **FR-201:** The bridge detects incoming text messages from the Messages database using a stable message identifier, message text, sender identifier, timestamp, and inbound/self direction metadata when available.
- **FR-202:** The watcher processes only inbound messages. Rows marked as sent by the local account, rows with an ineligible direction, and rows that cannot prove inbound direction are ignored and recorded without an API call.
- **FR-203:** A separate inbound sender allowlist controls eligibility. A sender must match an explicitly configured canonical identifier before its message can reach the agent. The existing outbound recipient allowlist remains in force for replies.
- **FR-204:** Unauthorized senders are ignored without an OpenAI request, outbound handoff, or sensitive-content log entry. Allowlist configuration errors fail closed with an actionable error.
- **FR-205:** The watcher persists processing state outside the Messages database. A stable message ID, or a documented deterministic fallback identity, must prevent the same inbound message from being processed more than once across restarts.
- **FR-206:** Duplicate detection must be atomic with state creation so two watcher invocations cannot both create a response for the same message. Reprocessing requires an explicit operator action and must be visible in the state record.
- **FR-207:** Before calling the agent, the system applies self-reply protections: inbound-only filtering, sender allowlist checks, and exclusion of messages whose sender/handle identifies the local account or configured reply identity. A generated response must not be fed back into the watcher as a new conversation turn.
- **FR-208:** Eligible message text is passed to `Agent.respond` using the configured model and system prompt. Offline mode must remain available for tests and must not call the OpenAI API.
- **FR-209:** The system creates a pending reply containing the source message ID, authorized sender, generated text, model/mode metadata, and creation time. It must present enough context for a user to review the proposed reply without exposing unrelated message history.
- **FR-210:** No reply is handed to Messages until an explicit approval action identifies the exact pending source message and candidate reply. Approval must invoke the existing outbound allowlist and `confirmed=True` gate.
- **FR-211:** Rejecting, expiring, or cancelling a pending reply must not invoke Messages or the OpenAI API and must leave an auditable terminal state.
- **FR-212:** Incoming message text, sender identifiers, generated replies, and API errors must not be written to normal logs by default. Diagnostics may include redacted IDs, status, counts, and error categories, but never API keys or full private message contents.
- **FR-213:** OpenAI credentials are obtained only through the existing client’s supported environment/keychain configuration. The feature must not accept credentials in message text, command arguments, persisted processing state, or logs.
- **FR-214:** API calls use explicit cost controls: configurable model, maximum input size, maximum output tokens, per-run request limit, and a minimum inter-request interval or equivalent rate limit. Messages rejected by these controls are recorded without sending.
- **FR-215:** API timeouts, authentication failures, rate limits, quota errors, malformed responses, database permission errors, and state-store failures produce actionable categorized errors. A failed API or send operation must preserve enough state for a deliberate retry without causing duplicate delivery.
- **FR-216:** The watcher and approval workflow must never execute shell commands, AppleScript, subprocesses, or arbitrary tools based on incoming message content. Only the explicitly approved reply path may invoke the existing Messages handoff.
- **FR-217:** The CLI requires explicit activation before polling. First-run activation records a durable watermark for the latest text message and skips all messages at or before that boundary; a restart reuses the same watermark.
- **FR-218:** The CLI may load only `OPENAI_API_KEY` from the project-root `.env`, must never override an already-set environment variable, and must never print or persist the credential.
- **FR-219:** Pending-queue output omits sender identifiers and generated reply text by default. Private fields may be shown only through an explicit operator opt-in.

## Non-functional requirements

- **NFR-201 — Least privilege:** Messages access is read-only during detection; outbound sending is approval-gated and allowlisted.
- **NFR-202 — Privacy:** Private messages and credentials are excluded from logs, tests, fixtures, documentation, and version control by default.
- **NFR-203 — Determinism:** Unit tests use injected bridge, agent, clock, and state-store dependencies; no test requires Messages, an iPhone, or a live OpenAI request.
- **NFR-204 — Recoverability:** A process restart must not lose pending approvals or cause an already sent message to be sent again.
- **NFR-205 — Observability:** Operators can inspect redacted status, counts, timestamps, and failure categories without reading message bodies.

## Acceptance criteria

1. Given an inbound message from an allowlisted sender, the watcher creates exactly one persisted processing record and one pending reply candidate; no outbound Messages call occurs before approval.
2. Given a sender absent from the inbound allowlist, the watcher records `ignored` (or equivalent), makes zero OpenAI requests, and makes zero outbound handoffs.
3. Given a database row marked as sent by the local account or lacking provable inbound direction, the watcher ignores it and makes zero OpenAI requests and zero outbound handoffs.
4. Given the same eligible message is observed at least twice, including after a process restart or concurrent watcher invocation, exactly one candidate is created and exactly one API request is made.
5. Given a pending candidate, explicit approval for that candidate invokes the outbound allowlist and existing confirmation gate exactly once; rejection invokes neither the API nor Messages.
6. Given a generated reply or incoming message containing shell-like text, no subprocess, shell, or arbitrary tool is invoked because of that content.
7. Given missing credentials, API timeout, rate limit, quota failure, malformed API output, or Messages database permission failure, the system records a categorized failure, emits no secret or full message body, and does not claim delivery.
8. Given configured cost limits, the watcher never exceeds the per-run request limit, maximum input/output bounds, or configured request interval; over-limit messages remain unsent and are auditable.
9. Given an already sent source message or a message identified as a self-reply, a subsequent watcher run performs no API request and no outbound handoff.
10. The complete automated Feature 002 test suite passes with no network, Messages database, AppleScript, credentials, or physical device dependency.
11. On first run, polling before activation fails closed; explicit activation records the latest available watermark and returns no historical messages. A later message is eligible, while a restarted processor continues from the same watermark.
12. A project-root `.env` key is loaded only when `OPENAI_API_KEY` is absent from the environment; an existing environment value wins, and neither value appears in CLI output or logs.
13. Default pending-queue output contains only redacted identifiers/status and excludes private sender and reply text.

## Out of scope

- Unattended outbound message sending.
- Executing commands, tools, or code requested by an incoming message.
- Reading attachments, images, reactions, group membership, or non-text content unless separately specified.
- Live OpenAI credential provisioning or credential storage.
- iPhone app creation, Xcode signing, or device installation.
