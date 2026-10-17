# Security policy

*[한국어 / Korean: SECURITY.ko.md](SECURITY.ko.md)*

## Supported versions

Security fixes target the latest GitHub release and the current `main` branch.
Older pre-1.0 releases may not receive backports.

## Reporting a vulnerability

Please use [GitHub private vulnerability reporting](https://github.com/mud-the-developer/mudplot/security/advisories/new).
Do not open a public issue for an unpatched vulnerability.

Include the affected version, a minimal reproduction, impact, and any suggested
mitigation. Please omit secrets and sensitive research data. You should receive
an initial response within seven days.

## Release verification

Starting with v0.6.0, releases require a GitHub-verified signed annotated tag
and include `SHA256SUMS` plus GitHub OIDC build-provenance attestations for the
wheel, sdist, and checksum file. After
downloading the assets, verify them with:

```bash
sha256sum --check SHA256SUMS  # macOS: shasum -a 256 -c SHA256SUMS
gh attestation verify ./mudplot-*.whl --repo mud-the-developer/mudplot
gh attestation verify ./mudplot-*.tar.gz --repo mud-the-developer/mudplot
gh attestation verify ./SHA256SUMS --repo mud-the-developer/mudplot
```

## Local editor boundary

The Python and Rust editors are unauthenticated, single-user local tools. They
enforce loopback binds/HTTP Hosts and reject cross-origin mutations, but they
must not be exposed through a reverse proxy, tunnel, or public port. Use an
authenticated service designed for remote access if that need arises.

Same-origin browser mutations and local agent requests without an Origin header
are supported; cross-site fetch metadata or a mismatching/null Origin is rejected.
This policy is not authentication. Application responses, including rejected
Host/Origin requests, carry no-store/CSP headers. Malformed HTTP rejected before
application routing is a separate transport boundary.

Declared bodies over 16 MiB are rejected before upload/read. Python accepts
Content-Length framing only: unsupported Transfer-Encoding, duplicate lengths
and incomplete bodies fail before actions. Rust caps decoded bodies before all
handlers (including undo/reset) and accepts bounded chunked requests.

Sequential local form/JSON boundary probes cover N-1/N/N+1 and record server-PID
RSS/lifetime peaks; native renderer descendants are excluded. These observations
are not hard memory/CPU limits, concurrent-load guarantees or proof on every OS.
See [the review ledger](docs/REVIEW_CHECKLIST_STATUS.md) for exact scope/results.
