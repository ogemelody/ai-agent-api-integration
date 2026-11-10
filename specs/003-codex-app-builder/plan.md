# Implementation Plan

## Phase 0 — Prerequisites and contracts

Verify that Feature 002 is merged into `main` before implementation integration. Preserve its activation watermark, sender allowlist, deduplication, explicit outbound approval, redaction, and watermark-aware polling contracts. Define Feature 003 typed models for requirement drafts, approvals, jobs, artifacts, worker results, progress events, errors, and cancellation.

## Phase 1 — Personal MVP domain and durable state

Add a local job store with schema-versioned records, monotonic transitions, attempt IDs, approval records, cancellation requests, artifact manifests, relative workspace paths, timestamps, redacted failure categories, and safe status summaries. Use atomic compare-and-set transitions so duplicate messages, approvals, retries, and restarts are idempotent. Keep message bodies and credentials out of the job store.

## Phase 2 — Clarification and approval workflow

Build a bounded clarifier that converts an authorized app request into a structured requirement draft and asks only the missing questions needed for generation. Bind generation approval to a canonical draft hash. Invalidate the approval when the draft changes. Route every status or question through the existing Feature 002 approval-gated iMessage channel.

## Phase 3 — Isolated Codex generation worker

Define a replaceable `CodexWorker` interface with validated input, timeout, cancellation, cost budget, workspace root, and output manifest. Implement a local fake worker first, then a guarded Codex adapter only after explicit approval. Create a fresh workspace beneath the configured root, enforce path and symlink restrictions, and validate source/test/project outputs without executing them. Redact worker errors and keep credentials in the supported secret source.

## Phase 4 — Generated artifact validation and separate execution gates

Validate that generated output contains SwiftUI source, tests, project metadata, an allowed manifest, and no forbidden paths or secret-like content. Add separate approval-bound commands for running tests/builds, signing, installing, and publishing. Reuse the existing Apple/Xcode preflight where applicable, but do not invoke any of these operations during generation.

## Phase 5 — Progress, cancellation, and recovery

Add bounded progress events, heartbeats, timeout handling, cancellation propagation, cancellation grace periods, retry policies, and safe redacted status messages. On restart, reconcile durable job state with worker leases and never infer success from process disappearance. Keep successful handoff, build, signing, installation, publication, and device delivery as separate evidence claims.

## Phase 6 — Portability seams

Keep local implementations behind protocols. Specify adapters for SQS job dispatch, S3 artifact storage, DynamoDB job state/idempotency, and dedicated EC2 Mac workers, without provisioning or integrating them in the personal MVP. Reserve account/tenant, quota, workspace, and role fields for future classroom accounts while keeping personal defaults simple.

## Verification strategy

- Unit-test state transitions, canonical draft hashing, approval binding, redaction, path validation, cost/time limits, cancellation, and idempotency.
- Contract-test fake and local adapters against the same worker/store/channel protocols.
- Use fixture SwiftUI source and test trees only; never include private Messages data, credentials, or real generated project secrets.
- Run `uv run pytest` before the Feature 003 implementation milestone is considered locally complete.
- Document any unavailable Codex, Xcode, Apple, AWS, or device capability as blocked rather than mocked as completed.

## Risks and mitigations

- **Prompt or code injection:** treat messages and generated files as untrusted data; use structured inputs, isolated workspaces, allowlisted outputs, and no implicit execution.
- **Credential leakage:** use environment/keychain/secret-manager references, never prompts or job fields; redact errors and command output.
- **Runaway spend:** enforce request, token, file, wall-clock, and per-job budgets before worker calls.
- **Partial work:** persist transitions and leases; make retries explicit and idempotent; never skip approvals after restart.
- **Unsafe paths:** resolve paths beneath the workspace root and reject traversal, symlink escapes, absolute paths, and unexpected file types.
- **Mac coupling:** isolate Apple/Xcode actions behind approval-gated adapters and preflight checks.
- **Future scale complexity:** keep AWS and classroom concerns at protocol boundaries until the personal MVP is proven locally.
