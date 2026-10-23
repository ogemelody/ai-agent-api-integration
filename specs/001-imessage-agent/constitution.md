# Constitution: iMessage AI Agent

## Principles

1. **Verification over assertion.** The agent distinguishes simulated, prepared, and completed actions. iMessage delivery, device installation, and signing are never claimed without an observed result.
2. **Least privilege.** Message access is read-only by default. Sending is restricted to an explicit allowlist and confirmation gate. Credentials remain in environment/keychain-managed stores.
3. **Spec before implementation.** Every feature has written requirements, a plan, tasks, and tests before completion.
4. **Human approval at irreversible boundaries.** Sending messages, changing Apple signing configuration, using credentials, and installing on a device require explicit approval.
5. **Affordable and observable API use.** The default model is economical, calls are isolated behind a client, and offline tests do not spend API credits.

## Quality gates

- `uv run pytest` must pass before a milestone is locally complete.
- Any unavailable Mac permission, Xcode installation, Apple account, or iPhone is documented as blocked rather than mocked as success.
- Secrets are excluded from version control and never printed.
