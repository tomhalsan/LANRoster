# LANRoster Roadmap

## Current state

LANRoster is currently at **v0.2.0**.

The current release demonstrates the core product idea:

- discover devices on a trusted local IPv4 network;
- combine several local identity signals;
- classify and preserve devices;
- track online and asleep state;
- store the roster in SQLite;
- inspect services;
- maintain user-controlled nicknames and notes;
- present the roster through a local web dashboard and API.

The path to v1.0 focuses first on trust, security, identity correctness,
recovery, maintainability, and reproducible distribution.

GitHub milestone membership is authoritative if this document and GitHub ever
differ.

## Release principles

LANRoster v1.0 should be:

- **Local-first:** Household network data remains local by default.
- **Privacy-preserving:** External processing is optional, bounded, and
  transparent.
- **Safe by default:** Localhost-first access and restricted network actions.
- **Evidence-aware:** Identity claims preserve provenance and uncertainty.
- **Recoverable:** Database migrations, backup, export, and restore are
  supported.
- **Maintainable:** Clear architecture boundaries and focused tests.
- **Evidence-based:** Compatibility claims come from observed results.
- **Reproducible:** Release artifacts are built and verified through
  automation.
- **Human-governed:** Security-sensitive and external-enrichment decisions
  require explicit approval.

No milestone has a promised delivery date.

## v0.3: Security and stabilization

Issues #9 through #17.

Goals:

- establish the authoritative v0.2 validation baseline;
- align documentation with the current implementation;
- add standard packaging and CI;
- make localhost the default;
- restrict subnet and device targets;
- protect state-changing operations;
- use UTC-aware durable timestamps;
- separate presence scanning from enrichment;
- add privacy-safe diagnostics.

## v0.4: Durable identity and recovery

Issues #18 through #21.

Goals:

- distinguish network observations from logical devices;
- preserve identity evidence, provenance, confidence, and conflicts;
- add versioned SQLite migrations;
- support backup, export, restore, and failure recovery;
- introduce a versioned public API;
- provide sanitized diagnostic exports.

## v0.5: Maintainability and user experience

Issues #22 through #25.

Goals:

- move dashboard markup into conventional templates and static assets;
- split tests by architectural layer;
- implement a calm and accessible dashboard;
- improve first-run, degraded-mode, and recovery guidance.

## v0.8: Governed optional capabilities

Issues #26 through #28.

Goals:

- add authorized Wake-on-LAN for known eligible devices;
- add opt-in, rate-limited latency measurement;
- decide whether external vendor and AI enrichment should exist.

## v0.9: Release candidate

Issues #29 through #33.

Goals:

- define supported install, upgrade, uninstall, and service workflows;
- validate supported operating systems and Python versions;
- complete the v1.0 threat model and security review;
- add contribution, conduct, security, support, and privacy documentation;
- run a multi-day release-candidate field test;
- resolve all P0 and P1 release blockers.

## v1.0: Stable free distribution

Issues #34 and #35.

Goals:

- build release artifacts from tagged automation;
- run tests, linting, typing, dependency, and secret checks;
- produce wheel and source archives;
- produce checksums and provenance metadata;
- generate accurate release notes;
- perform a final human-controlled readiness review;
- publish v1.0.0 only after explicit approval.

## Scope discipline

The following are not automatically part of v1.0:

- cloud-hosted operation;
- enterprise multi-subnet management;
- autonomous response or remediation;
- external AI enrichment without an accepted architecture decision;
- unsupported platform claims;
- public-internet exposure;
- silent transmission of household network data.
