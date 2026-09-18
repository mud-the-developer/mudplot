# 보안 정책

*[English: SECURITY.md](SECURITY.md)*

## 지원 버전

보안 수정은 최신 GitHub release와 현재 `main` branch를 대상으로 합니다.
이전 pre-1.0 release에는 backport하지 않을 수 있습니다.

## 취약점 제보

[GitHub 비공개 취약점 제보](https://github.com/mud-the-developer/mudplot/security/advisories/new)를
사용하세요. 패치되지 않은 취약점을 public issue로 공개하지 마세요.

영향받는 version, 최소 재현 방법, 영향, 가능한 완화책을 포함하되 secret이나
민감한 연구 데이터는 넣지 마세요. 7일 이내 첫 답변을 목표로 합니다.

## Release 검증

v0.6.0부터 Release에는 GitHub-verified signed annotated tag가 필요하며
wheel, sdist, checksum 파일의 `SHA256SUMS`와 GitHub OIDC build-provenance
attestation을 제공합니다. asset을 내려받은 뒤 다음처럼 검증하세요.

```bash
sha256sum --check SHA256SUMS  # macOS: shasum -a 256 -c SHA256SUMS
gh attestation verify ./mudplot-*.whl --repo mud-the-developer/mudplot
gh attestation verify ./mudplot-*.tar.gz --repo mud-the-developer/mudplot
gh attestation verify ./SHA256SUMS --repo mud-the-developer/mudplot
```

## 로컬 editor 경계

Python/Rust editor는 인증 없는 단일 사용자 로컬 도구입니다. loopback
bind/HTTP Host를 강제하고 cross-origin mutation을 거부하지만 reverse proxy,
tunnel, public port로 노출하면 안 됩니다. 원격 사용이 필요하면 인증을 갖춘
별도 서비스를 사용하세요.
