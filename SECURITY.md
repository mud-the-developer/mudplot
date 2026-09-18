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
