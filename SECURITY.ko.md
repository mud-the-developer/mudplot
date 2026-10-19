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

Same-origin browser mutation과 Origin 없는 로컬 agent 요청은 지원하며 cross-site
fetch metadata 또는 불일치/null Origin은 거부합니다. 이는 인증 기능이 아닙니다.
Host/Origin 거부를 포함한 application 응답에도 no-store/CSP를 적용합니다.
Application routing 이전의 malformed HTTP 거부는 별도 transport 경계입니다.

선언한 body가16 MiB를 넘으면 업로드/읽기 전에 거부합니다. Python은 Content-Length
framing만 지원하며 Transfer-Encoding·중복 길이·불완전 body는 action 전에 거부합니다.
Rust는 undo/reset을 포함한 모든 handler 전에 decoded body 한도를 적용하며 한도 내
chunked 요청을 지원합니다.

로컬 순차 form/JSON N-1/N/N+1 probe와 서버 PID RSS/수명 peak를 관찰했으며 native
렌더 자식은 제외했습니다. 이는 메모리/CPU hard limit·동시 부하·모든 OS 보장이 아닙니다.
정확한 범위/결과는 [리뷰 대장](docs/REVIEW_CHECKLIST_STATUS.md)을 확인하세요.

## 계산과렌더자원

요청bytes한도는CPU/RAM/렌더계산량budget이아닙니다. Preview는한축2000pixel로제한되지만
구조복잡도/정확한크기export는훨씬큰작업을요구할수있습니다. 가져오는spec/data를신뢰하고
untrusted/매우큰작업은호출자가관리하는resource-limitedprocess에격리하며처리service로노출하지마세요.

Hist2d는축당최대512bins(513edges),hexbin은gridsize최대512를지원하고초과는clamp나
nativequadraticallocation이아닌validation에서거부합니다. 이것이전체memory/timehardlimit는
아닙니다. Figure/layout은최대256panels/cells이며생성index0..255의자동확장은유지하되
초과확장/rawpanelarray는대량PanelSpec생성전에거절합니다. Ownedrender/save는backend/outputDPI와
padding포함tightbbox의canvas40millionpixels초과를native작업전에거절합니다. SourceDPI한도가
아니라원spec/cappedpreview는유지하고출력을조용히downscale하지않습니다. Figure전체는
최대1024layers이며초과raw배열/AddLayer/facet·joint확장을개별decode/newcopy/bulk복제전
거절합니다. 다른text/algorithm/CPU/전체memory정책은검토중이며리뷰probe의WindowsJob제한은시험격리이지
제품에설치된sandbox가아닙니다. 미패치stresspayload는private로보관합니다.

## 파일과 실행 경계

HTTP static/export route는 고정 bundled 자산이나 현재 figure bytes만 선택합니다.
URL/query 경로가 서버 파일이나 출력 목적지를 고르지 않습니다. Local API/CLI export는
지원 symlink 해석을 포함해 호출자가 명시한 경로를 유지하므로 신뢰하는 출력 directory를
선택하세요. JSON/PNG/PDF/SVG staging은 생성 이름을 배타적으로 소유한 뒤 쓰기/정리를
하며 기존 entry면 실패합니다. 적대적인 shared directory sandbox나 PGF sidecar 묶음의
atomic transaction을 보장하는 것은 아닙니다.

JSON은 pickle/object 복원이 아닌 plain data입니다. DOI/arXiv/reference는 offline 문자열
정규화이며 일반 PNG/PDF/SVG 링크는 output annotation이지 서버 fetch가 아닙니다.
실행 가능한 위험 scheme/citation escape는 validation이 거부하며 허용 링크를 누르는
동작은 viewer 사용자의 명시적 행동입니다. 명시적 TeX/PGF는 설정한 local TeX engine을
실행하므로 신뢰하는 입력/도구만 사용하세요. 임의 Python 호출이나 untrusted TeX의
sandbox를 제공하지 않습니다.

## 진단과 의존성 검사

기본 editor log는 제출 spec/draft/query 값을 의도적으로 기록하지 않습니다. 같은
로컬 client의 오류 진단·현재 state·draft 응답은 편집 기능이지 credential 보관소나
사용자 간 기밀성 경계가 아닙니다. 실제 token을 그림 데이터/URL에 넣지 마세요. Debug
도구·custom observer·proxy·호출자가 요청한 CLI 출력은 별도 노출 검토가 필요합니다.

의존성 checker는 세 committed Python lock export를 audit합니다. 제한된 OSV snapshot은
Cargo.lock의 registry crate도 대조하지만 local/git/private source와 advisory 외 범주는
별도 검토해야 합니다. Clean snapshot은 조회 당시 버전에 알려진 advisory가 반환되지
않았다는 뜻이며 보안 승인이나 후속 사용자 dependency resolution의 보장이 아닙니다.
