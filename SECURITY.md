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

## Compute and render resources

A request-byte limit is not a CPU/RAM/render-work budget. Preview output is
bounded to 2000 pixels per axis, but structural complexity and exact-size
exports can require substantially more work. Keep imported specs/data trusted;
contain untrusted or unusually large work in caller-managed resource-limited
processes rather than exposing these editors as a processing service.

Bivariate hist2d now supports at most512bins per axis (513edges), and hexbin
supports gridsize up to512; oversized requests fail validation rather than being
clamped or reaching native quadratic allocation. This specific guard is not a
hard total memory/time limit. Figures/layouts are also limited to256panels/cells;
creating indices0..255 still autoextend, while larger expansion and raw panel
arrays fail before bulk PanelSpec construction. Other complexity/exact-export
resource policy remains under review; Windows Job limits in review probes are test containment,
not an installed application sandbox. Unpatched stress payloads are kept private.

## File and execution boundaries

HTTP static/export routes select fixed bundled assets or return current figure
bytes; URL/query paths do not select server files or output destinations. Local
API/CLI exports still use the caller's explicit path, including supported symlink
resolution; choose a trusted output directory. JSON/PNG/PDF/SVG staging exclusively
claims its generated file before writing/cleanup and fails on an existing entry.
This is not an adversarial shared-directory sandbox or an atomic PGF sidecar bundle.

JSON is plain data, not pickle/object restoration. DOI/arXiv/reference handling is
offline normalization; ordinary PNG/PDF/SVG links are output annotations, not server
fetch requests. Unsafe active link schemes/citation escapes are rejected by
validation. Clicking a permitted output link is the viewer's explicit action.
Explicit TeX/PGF workflows run a configured local TeX engine and are not a sandbox
for untrusted TeX or arbitrary Python callers; keep those inputs/tools trusted.

## Diagnostics and dependency checks

Default editor logging does not intentionally record submitted specs, drafts or
query values. Same-client error diagnostics/current-state/draft responses remain
part of editing, not a credential store or cross-user confidentiality boundary.
Do not put real tokens in figure data or URLs. Debug tooling, custom observers,
proxies and caller-requested CLI output need their own disclosure review.

The dependency checker audits three committed Python lock exports. A bounded OSV
snapshot also covers registry crates in Cargo.lock; local/git/private sources and
non-advisory categories require separate review. A clean snapshot means no known
advisory was returned for the queried versions at that time, not security approval
or coverage of later user dependency resolution.
