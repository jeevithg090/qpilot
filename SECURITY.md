# Security policy

qPilot is research software for analysing qPCR data on your own computer. **It is for research use only and is not intended for clinical or diagnostic use.**

## Supported versions
| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a vulnerability
Please report vulnerabilities privately through GitHub's **"Report a vulnerability"** button on this repository's **Security** tab (private vulnerability reporting). Do not open a public issue for a security problem.

We follow **coordinated disclosure**: we aim to acknowledge a report within 5 working days and to publish a fix or mitigation within 90 days, after which the reporter may disclose publicly. We will credit reporters who wish to be credited.

## Scope
In scope: the `qpilot` Python package and its command-line interface, and (once they ship) the local web app and the MCP server.

Design rules:
- RDML input is untrusted: the loader (not implemented yet) must parse XML without resolving external entities, loading DTDs or touching the network (`tests/fixtures/xxe.rdml` is the regression fixture for this).
- Unit tests run with network access disabled (`pytest-socket`).
- No credentials are stored in the repository; `gitleaks` runs as a pre-commit hook.
