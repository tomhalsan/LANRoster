# AGENTS.md

## Scope

These instructions apply to the entire LANRoster repository.

## Project boundaries

- Preserve Clean Architecture dependency direction.
- Domain code must not depend on Flask, Scapy, SQLite, sockets, or operating-system commands.
- Use ports to expose infrastructure capabilities to use cases.
- Keep concrete runtime wiring in the composition root.
- Do not implement planned roadmap capabilities unless the associated GitHub issue is in scope.

## Privacy and security

- Do not commit real IP addresses, MAC addresses, hostnames, device aliases, notes, router details, database contents, packet captures, or live scan output.
- Use synthetic or sanitized fixtures in tests and documentation.
- Keep external lookup optional, transparent, and separate from local authoritative state.
- Do not add new external data transmission or network mutation capability without an explicit security and privacy review.
- Do not expose the development server to the public internet.

## Development workflow

- Start from a named branch based on current `main`.
- Keep changes bounded to the approved issue.
- Run Python commands through the repository virtual environment. Do not assume shell activation.
- Prefer explicit commands such as `.venv/bin/python -m unittest discover tests` and `.venv/bin/pyrefly check`.
- Keep deterministic tests rootless and independent of live network hardware.
- Classify any live-network validation as explicit and opt-in.
- Run `git diff --check` before committing.
- Do not stage, commit, push, open a pull request, or merge without human approval.

## Validation

The minimum rootless validation set is:

```bash
.venv/bin/python -m unittest discover tests
.venv/bin/pyrefly check
git diff --check
```

Run additional boundary, persistence, API, or platform tests when the changed area requires them.

## Documentation

- Keep the README, architecture, roadmap, and issues naturally consistent.
- Distinguish implemented, planned, experimental, and optional capabilities.
- Do not make unverified compatibility, performance, security, or production-readiness claims.
- Update documentation when architecture, operational behavior, or release scope changes.

## IDE or AI tool usage

- Select an IDE or coding agent based on task fit, cost, capacity, privacy, and the value of its repository context.
- Before and after any IDE or coding-agent session, capture the provider's available usage evidence when such evidence is available.
- Record the tool, model, effort or reasoning level, elapsed time, repository baseline, files changed, validation result, and human acceptance.
- Pass the raw usage output and a short task summary to the project's Tiny Capacity Lab notepad.
- Do not infer missing quotas, reset times, usage, or cost. Unknown values remain unknown.
