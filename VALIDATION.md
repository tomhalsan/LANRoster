# LANRoster Validation Baseline

## Baseline

- Collected at: 2026-11-18T06:43:51Z
- Local time: 2026-11-17T22:43:51-08:00
- Branch: chore/issue-9-validation-baseline
- Commit: d0ccf54f7cb60b4fc83dd28fec6fb5681a696623
- Platform: macOS 27.2.1, Apple ARM64
- Python: 3.14.8
- pip: 26.2.2
- Pyrefly: 1.4.0
- Scapy: 2.8.0

- Working tree was clean before and after validation.

## Rootless unit tests

Command:

```bash
.venv/bin/python -m unittest discover tests
```

Result:

- 51 tests passed.
- Unittest reported 0.155 seconds.
- Observed wall time was 1.474 seconds.

## Static typing

Command:

```bash
.venv/bin/pyrefly check
```

Result:

- 0 errors.
- Observed wall time was 0.857 seconds.

## Non-elevated startup

The startup probe used a temporary home directory and did not use sudo.

Observed behavior:

- The Flask development server started.
- The v0.2 entry point listened on all host interfaces at port 8000.
- The background ARP sweep failed because the process could not open macOS /dev/bpf0 without elevated permissions.
- The web process remained running in a degraded state until the probe stopped it.
- The temporary home contained the test SQLite database and Scapy cache files.
- The repository working tree remained clean.

## Known validation boundaries

- The unit tests do not require root privileges or live network access.
- The startup probe validated macOS only.
- The probe confirmed degraded behavior when macOS packet capture permission was unavailable.
- This baseline does not establish Windows, Linux, browser, distribution, performance, or production-deployment support.

## Reproduction

Run the rootless validation with:

```bash
.venv/bin/python -m unittest discover tests
.venv/bin/pyrefly check
git diff --check
```

Live startup probes must use a temporary home directory or another explicit isolation boundary so user data is not modified.
