# Tasks

## Phase 0 — Prerequisites and contracts

- [ ] T301 Verify Feature 002 is merged into `main`; record the commit and preserve its polling, activation, sender-policy, approval, and redaction contracts.
- [ ] T302 Define Feature 003 domain models, job state machine, approval boundaries, error categories, and safe progress event schema.
- [ ] T303 Define replaceable protocols for conversation channel, requirement clarifier, job store, workspace manager, Codex worker, approval provider, and artifact validator.

## Phase 1 — Personal MVP state and clarification

- [ ] T304 Add a local schema-versioned job store with atomic compare-and-set transitions, attempt IDs, leases, cancellation, and restart recovery.
- [ ] T305 Add canonical requirement drafts and bounded clarification questions for app name, target, flow, screens, data, accessibility, and unknowns.
- [ ] T306 Bind generation approval to the exact normalized draft hash and invalidate approval after material edits.
- [ ] T307 Reuse Feature 002 authorization, deduplication, activation, sender filtering, outbound confirmation, and redacted status channel contracts.

## Phase 2 — Isolated generation

- [ ] T308 Add a workspace manager enforcing configured-root containment, fresh workspaces, path traversal rejection, symlink escape rejection, and cleanup policy.
- [ ] T309 Add a deterministic fake Codex worker for offline tests with timeout, cancellation, cost, output-file, and output-size limits.
- [ ] T310 Add the guarded Codex adapter with secure credential lookup, structured inputs, redacted errors, and no implicit code execution.
- [ ] T311 Validate generated SwiftUI source, project metadata, tests, allowed manifest, hashes, and secret/path safety before recording `generated`.

## Phase 3 — Separate execution approvals

- [ ] T312 Add distinct approval records and commands for running generated code/tests, signing, installing, and publishing.
- [ ] T313 Integrate existing Apple/Xcode preflight behind the execution/sign/install gates without changing signing configuration automatically.
- [ ] T314 Add safe progress, timeout, cancellation, heartbeat, retry, and failure reporting through the approval-gated iMessage channel.

## Phase 4 — Verification and future seams

- [ ] T315 Add tests for unauthorized requests, clarification, approval binding, duplicate requests, restarts, cancellation, redaction, path restrictions, and secret safety.
- [ ] T316 Add tests proving generation never runs code and that each later approval is independent and idempotent.
- [ ] T317 Add adapter contract tests for local implementations and document SQS/S3/DynamoDB/EC2 Mac worker seams without provisioning AWS.
- [ ] T318 Add future classroom-account extension points for tenant isolation, quotas, roles, workspaces, and audit retention without enabling multi-tenancy.
- [ ] T319 Run the complete automated suite, review artifacts for private data, and update `features.md` only after implementation evidence exists.
