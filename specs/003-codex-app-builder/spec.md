# Feature Specification: Melox iOS App Builder

## Goal

Extend the Feature 002 approval-gated iMessage channel into a personal MVP that can turn an authorized iMessage app request into a reviewable SwiftUI project. The system clarifies requirements, asks for explicit approval before generation, invokes Codex in an isolated workspace, generates real SwiftUI source and tests, persists job state, and reports only safe progress through the same approval-gated channel.

Feature 003 does not authorize unattended code execution, signing, installation, publishing, or outbound messaging. Feature 002 must be merged into `main` before implementation integration begins; this specification is prepared on the Feature 003 branch while that prerequisite remains unmerged.

## Scope and safety boundary

The MVP supports one personal operator and one authorized inbound sender policy inherited from Feature 002. It is an orchestration and generation workflow, not a general multi-tenant service. Generated artifacts are kept in an isolated project workspace under an explicitly configured root. The service never treats message text as shell input, never exposes credentials to Codex through prompts, and never claims that a build, signature, installation, publication, or delivery occurred without independent evidence.

Each irreversible or externally consequential boundary has its own approval:

1. approval to generate the app;
2. separate approval to run generated code or tests;
3. separate approval to sign an artifact;
4. separate approval to install on a device or simulator;
5. separate approval to publish or upload an artifact.

An approval for one boundary never implies approval for another.

## Assumptions

- The personal MVP runs on the existing Mac-hosted Python service and uses the Feature 002 conversation/state contracts after Feature 002 is merged into `main`.
- `main` means the latest local `main` ref unless a later workflow explicitly authorizes fetching or rebasing from a remote.
- Codex, OpenAI, Messages, and Apple credentials are provisioned outside this feature through the platform-supported secret mechanism; this feature never creates or stores them.
- A configured workspace root is writable by the service, while generated workspaces are disposable and isolated from the repository and user home directories.
- The personal operator is the only approver in the MVP; classroom accounts require the future account, role, quota, and audit extensions described below.
- AWS services and dedicated Mac workers are architectural seams only in this feature; no infrastructure or cloud account is assumed to exist.

## Actors and components

- **Requester:** sends an authorized iMessage describing an iOS app.
- **Conversation controller:** reuses Feature 002 sender filtering, activation, deduplication, approval, and safe status reporting.
- **Clarifier:** asks bounded follow-up questions and stores a structured requirement draft, without generating code.
- **Generation approver:** explicitly approves a normalized requirement draft for generation.
- **Codex worker:** replaceable worker that receives a validated job specification and writes source only inside an isolated workspace.
- **Job store:** durable state keyed by a non-sensitive job ID; it stores lifecycle metadata, redacted errors, timestamps, and artifact paths relative to the workspace root.
- **Operator:** approves generation, execution, signing, installation, or publishing independently and may cancel a job.
- **Future adapters:** queue, object storage, database, and dedicated Mac build workers may replace local implementations without changing the conversation contract.

## Job states

The durable state machine is monotonic except for explicit, auditable cancellation and retry actions:

`received` → `clarifying` → `awaiting_generation_approval` → `approved_for_generation` → `generating` → `generated` → `awaiting_execution_approval` → `testing` → `tested` → `awaiting_signing_approval` → `signing` → `signed` → `awaiting_install_approval` → `installing` → `installed` → `awaiting_publish_approval` → `publishing` → `published`

Terminal states are `cancelled`, `failed`, and `expired`. A job may stop at `generated`, `tested`, or `signed` without proceeding to the next approval boundary. Retries create an auditable attempt for the same job and may not bypass an approval.

## Functional requirements

- **FR-301:** The system accepts an app request only from an authorized inbound iMessage sender after Feature 002 inbound, self-reply, activation, and deduplication checks.
- **FR-302:** The system creates a redacted job ID and persists `received` state without storing unnecessary message history, credentials, or private logs.
- **FR-303:** The clarifier extracts a structured draft containing app name, target iOS range, primary user flow, required screens, data/storage assumptions, accessibility expectations, and explicit unknowns. It asks focused follow-up questions when required fields are missing or ambiguous.
- **FR-304:** Requirement clarification never invokes Codex, runs generated code, signs, installs, publishes, or sends a reply without the existing outbound allowlist and explicit confirmation gate.
- **FR-305:** The operator must explicitly approve the exact normalized requirement draft before a job can enter `approved_for_generation`. Edits or material requirement changes invalidate that approval.
- **FR-306:** Generation runs through a replaceable Codex worker interface in a fresh isolated workspace created beneath a configured project root. The worker may write only within that workspace and must reject path traversal, symlink escapes, absolute output paths, and writes outside the approved artifact set.
- **FR-307:** A successful generation job produces real SwiftUI source, an Xcode project specification or project, and deterministic unit/UI test source appropriate to the generated app. The result records a manifest of relative paths and content hashes without storing private message text.
- **FR-308:** Generation is bounded by configurable wall-clock timeout, input-size limit, output-file count/size limit, and cost/request budget. Exceeding a limit fails or cancels the job without continuing to later approval stages.
- **FR-309:** Running generated code, Swift tests, Xcode builds, or any generated executable requires separate explicit execution approval. Generation itself must not execute generated code.
- **FR-310:** Signing, installation, simulator/device interaction, and publication/upload each require separate explicit approval and applicable Apple/Xcode or destination preflight. The system must not change signing configuration or provision credentials automatically.
- **FR-311:** Job state transitions are durable and idempotent across process restarts. Duplicate iMessages, duplicate approvals, worker retries, and repeated status requests cannot create duplicate jobs or bypass a gate.
- **FR-312:** Cancellation is available before and during worker execution, has a bounded cancellation timeout, records the reason and final state, and prevents later stages from starting until a new explicit retry is approved.
- **FR-313:** Progress reports sent through iMessage contain only a redacted job ID, safe status, bounded counts, timestamps or duration, and categorized errors. They never contain API keys, `.env` contents, private message text, full prompts, raw stack traces, local absolute paths, or unredacted command output.
- **FR-314:** OpenAI, Codex, Apple, storage, and queue credentials are loaded only through supported environment/keychain/secret-manager mechanisms. Credentials are never accepted in iMessage text, persisted job state, worker arguments, generated source, logs, or status messages.
- **FR-315:** Worker failures are categorized as validation, timeout, cancellation, quota, authentication, workspace, tool, output-limit, preflight, or unknown failure. The operator receives a redacted recovery status and the job remains auditable.
- **FR-316:** The local MVP uses injected interfaces for the job store, clock, conversation channel, Codex worker, workspace manager, and approval provider. Future adapters may map jobs to SQS, artifacts to S3, state to DynamoDB, and execution to dedicated EC2 Mac workers without changing the domain state machine.
- **FR-317:** Classroom accounts are out of scope for the personal MVP but the job and authorization model must leave room for an account/tenant identifier, per-account quotas, isolated workspaces, role-based approvals, and separate audit retention.

## Non-functional requirements

- **NFR-301 — Least privilege:** the watcher is read-only; generation has workspace-only write access; execution, signing, installation, and publishing are separately gated.
- **NFR-302 — Privacy:** normal logs and iMessage status updates are redacted; private source text and generated source are not copied into the job database or chat transcript.
- **NFR-303 — Determinism:** offline tests use fake workers, stores, clocks, approvals, and channels; no test requires Messages, OpenAI, Codex, Xcode, AWS, or a device.
- **NFR-304 — Recoverability:** restart resumes from durable state without duplicating generation or crossing an approval boundary.
- **NFR-305 — Resource safety:** every external worker call has timeout, cancellation, output, and cost bounds.
- **NFR-306 — Portability:** local adapters are replaceable by AWS queue/storage/state and Mac worker adapters; domain code does not depend directly on AWS SDKs or shell commands.

## Acceptance criteria

1. An authorized inbound app request creates exactly one `received` job; an unauthorized sender creates no job and no Codex request.
2. A request with missing requirements receives bounded clarification questions and remains in `clarifying` until the draft is complete or cancelled.
3. No Codex call occurs before explicit approval of the exact normalized requirement draft.
4. A fake Codex worker can generate a SwiftUI source tree and tests entirely inside a temporary isolated workspace; path traversal and symlink escape attempts are rejected.
5. A successful generation records `generated`, a relative artifact manifest, hashes, worker metadata, and no private message body or credential.
6. Timeouts, cost limits, output limits, worker errors, and cancellation produce categorized redacted states and never advance the job to a later stage.
7. Running generated code/tests, signing, installing, and publishing each require a distinct approval; denying one does not affect the others.
8. Duplicate inbound requests, duplicate approvals, restarts, and worker retries remain idempotent and auditable.
9. Status messages expose only a redacted job ID, safe state, bounded progress, and categorized error information through the existing approval-gated Messages path.
10. Credentials are absent from prompts, job state, logs, generated files, command arguments, fixtures, and test output.
11. The full automated suite passes without network, Messages, Codex, AWS, Xcode, signing identities, or a physical device.
12. A contract test demonstrates that local worker/store/channel adapters can be replaced by future SQS/S3/DynamoDB and dedicated Mac worker adapters without changing job transitions or approvals.

## Out of scope

- AWS provisioning, deployment, queues, buckets, tables, or IAM changes.
- Running Codex, generated code, Xcode builds, signing, installation, or publication as part of this specification task.
- Multi-user classroom onboarding, billing, tenant administration, or shared workspaces.
- Arbitrary repository modification, general-purpose shell execution, or unattended app delivery.
