# v1.1.0 로컬 후보 체크리스트

*[English](V1_1_RELEASE_CHECKLIST.md)*

**현재 상태: 수치·출력 안전성을 강화한 1.1.0 후보의 전체 로컬 검증 완료.**
발행된 release나 배포 승인이 아닙니다. 작업은 로컬 미커밋 상태이며
push·PR·merge·태그·발행은 하지 않았습니다.

## 확정 범위

- 현재 구현·문서화된 부분 지원과 agent용 과학 그림 품질 개선을 포함합니다.
  B2b/B3/B4/B5/B6 미구현 확장은 후속 백로그이며 완료로 표시하지 않습니다.
- Matplotlib, 기존 Python/CLI 기본 동작, FigureSpec/JSON schema 0.1,
  이전 spec migration과 원본 측정값을 유지합니다. 이번에 plot type을 추가하지 않았습니다.
- `smart` / `smart-print`, `recommend()`, visual lint는 Python/CLI 기능입니다.
  Rust smart 토글은 필요 없고 기존 편집기 호환성을 검증합니다.
- 사용자 승인 보안 예외: Python >=3.11, 색상·렌더 NumPy >=1.23.5,
  Matplotlib >=3.8, 렌더 Pillow >=13.0.0. Python 3.10 지원 종료를 명시합니다.
- 원격 CI는 현재 개발 조건이 아닙니다. Windows는 보류이며 검증 완료나 영구 미지원을
  주장하지 않습니다. 실제 발행은 별도입니다.

## 검증 게이트

| ID | 상태 | 근거·범위 |
| --- | --- | --- |
| R01 | PASS | 사용자가 정한 구현 범위·보안 지원 예외 승인 |
| R02 | PASS | 새 locked 전체 검증: 3.11/3.12 각각 4547 통과·45 skip·실패 0 |
| R03 | PASS | 새 pinned 최소 환경 전체 3735 통과·36 skip·실패 0 |
| R04 | PASS | 필수 실제 브라우저와 품질 강화 후 Rust HTTP/browser/bridge/body 경계 통과 |
| R05 | DEFERRED | 로컬 Rust fmt/clippy/test·Rust 1.88 all-targets 통과; Windows는 사용자 지시로 보류 |
| R06 | PASS | 필수 PGF/reference·pdflatex/lualatex/tectonic/biblatex 논문 경로 통과 |
| R07 | PASS | 합성 4종 300-DPI before/after: 데이터·크기 유지, >=8-pt, after 구성 오류 0 |
| R08 | PASS | sdist 과학 그림 8개 필수 포함·설치된 기본/smart/CLI 검사 통과; 최종 hash·재빌드 증명은 외부 manifest; 의존성·정적 검사 통과 |
| R09 | PENDING | 그림·제한사항과 발행 여부의 사용자 검토; 외부 승인으로 주장하지 않음 |
| R10 | NOT REQUIRED | 현재 로컬 개발에 원격 CI 조건 없음; 원격 작업 실행 없음 |
| R11 | PASS | Python/Rust/Cargo.lock/uv.lock/README/changelog의 1.1.0 후보 일치; preflight·metadata/policy 관련 40개 통과 |
| R12 | OWNER APPROVAL | 서명 태그·실제 발행 승인이나 실행 없음 |

`PASS`는 기록한 소스·환경·범위에 한합니다. skip은 그대로 보존하며 상세 감사
장부의 ID를 일괄 PASS 처리하지 않습니다.

## 새로 고정한 전체 구현 checkpoint

| 환경 | 실행 | 통과 | Skip | 실패·오류 |
| --- | ---: | ---: | ---: | ---: |
| Locked Python 3.11 | 4592 | 4547 | 45 | 0 |
| Locked Python 3.12 | 4592 | 4547 | 45 | 0 |
| Pinned 최소 Python 3.11 | 3771 | 3735 | 36 | 0 |

Pinned Ubuntu에 tzdata·Chromium 실행 파일과 의존성·전체 TeX 도구 및 checksum을
확인한 Tectonic 0.15.0을 준비했습니다. 필수 report profile과 무관한 실패 거부
조건까지 통과했습니다. 이번에는 이전 1.0.0 표기가 아닌 1.1.0 버전 자체를
전체 검증했습니다.

이번 첫 실행에서는 세 환경 모두 옛 PGF 한계 확인 테스트 하나만 실패했습니다.
이 테스트는 후처리 실패 시 기존 파일이 덮어써지기를 기대했습니다. 사용자가
그 한계를 임시 작성·백업·실패 복구로 개선하도록 명시적으로 승인했으므로,
이제 기존 PGF·PNG 보존을 검증하게 갱신했습니다. 두 실행 사이 런타임 코드는
바꾸지 않았습니다. 실제 TeX 사전 검사 후 세 전체 suite를 모두 다시 실행해
통과했으며, 최초 실패 XML·log는 그대로 보존했습니다.

이번 checkpoint는 정확한 부동소수 프로필 보간·보조축 QA·PGF 실패 보호를 포함합니다.
실제 raster PGF와 논리 symlink 출력은 논문으로 컴파일되고 반복 저장 바이트가 같습니다.
Runtime·테스트·config·lock은 최종 고정 snapshot과 같습니다. 이후 갱신은 이 양언어
체크리스트·생성 report의 안내문 두 곳·새 receipt뿐입니다. PNG 8개와 측정값은
바이트 단위로 같습니다.

현재 근거: [수치·출력 품질 receipt](review_evidence/v1_1_numeric_export_quality.json).
[이전 배포](review_evidence/v1_1_distribution_quality.json)·[런타임](review_evidence/v1_1_quality_hardening.json)
receipt는 각 snapshot의 근거로 그대로 유지합니다. Raw report/log·최종 hash는 현재
receipt에 적힌 ignored 폴더에 보존하며, `.pi`·`artifacts`·비공개 출력 임시 파일과
백업은 배포물에서 제외합니다. Windows·원격 CI 검증을 주장하지 않습니다.

## 구현한 과학 그림 보호 장치

- 실제 범례·데이터 경계를 측정하고, 안전한 직접 라벨·공유 범례·외부 배치를 적용한
  뒤 다시 draw하여 검증합니다.
- 직접 라벨의 색은 합성된 실제 fill과 기존 linear-sRGB 엔진으로 고릅니다.
- 정수 프로필·정수 중앙값·IQR 경계·시간 순서·event offset을 보존하고 float 좌표
  정밀도 한계는 경고로 구분합니다.
- 지원 정밀도를 넘는 ISO 시각·offset은 반복 시각으로 오판하지 않고 경고합니다.
  시간 결측값은 예외를 내지 않으며 비숫자 입력을 시간으로 몰래 변환하지 않습니다.
- 짝 비교에는 유한한 측정값과 완전한 식별자를 요구합니다. role 길이 불일치는 거부하고,
  사용 가능한 좌표·측정값 쌍이 없으면 추천하지 않습니다.
- 시각 검사는 저널 최소 글자 크기와 실제 투명도를 따르며 해치 전용 도형·대체 marker
  면을 보존합니다. parser가 버리는 분수 UTC offset을 포함해 회귀 41개를 추가했습니다.
- 회귀 54개를 추가하여 극소·혼합 수치의 중앙값·IQR, 보조축 설명, 비공개 임시 파일,
  PGF 복구·오류 안내, 확장자 없는 CLI 실제 경로를 검증합니다. 원본 관측값·scalar 타입은 유지합니다.
- PGF 부속 파일의 성공 경로·이름을 유지하고 일반 실패에서는 기존 파일을 복구합니다.
  복구까지 실패하면 백업을 남겨 CLI로 알립니다. 동시 독자의 다중 파일 원자성이나
  강제 종료 후 내구성을 보장하지는 않습니다.
- 측정값 변경·단위 추측·outlier 제거·유의성 주장·geometry 자동 교체는 하지 않습니다.
  smart 정책은 spec field가 아닌 렌더 시점 옵션입니다.

## 과거 근거와 남은 한계

이전 실패·skip 기록은 그대로 유지합니다:
[최초 의존성 차단](review_evidence/v1_1_dependency_blocker.json),
[보안 해결](review_evidence/v1_1_security_resolution.json),
[이전 로컬 checkpoint](review_evidence/v1_1_local_validation.json),
[이전 로컬 후보](review_evidence/v1_1_local_candidate.json),
[정수 추천](review_evidence/v1_1_agent_precision.json),
[ISO 정밀도](review_evidence/v1_1_agent_precision_iso.json).
새로운 clean 결과로 과거 snapshot을 green으로 바꿔 표시하지 않습니다.

QA는 결정적 구성 검사이며 접근성·통계 인증이나 실제 논문·도메인 검토를 대신하지
않습니다. 실패 예제는 합성 데이터이며 원본 실패 dataset은 전달받지 않았습니다.
기존 CPU/RAM/history/inline-data 한계는 유지하며 streaming·sandbox SLA를 약속하지 않습니다.

[과학 그림 품질](SCIENTIFIC_QUALITY.md), [호환성](COMPATIBILITY.ko.md),
[기능 범위](FEATURE_COVERAGE.ko.md), [개발 이력](V1_1_PLAN.ko.md),
[감사 장부](REVIEW_CHECKLIST_STATUS.md), [개발자 실행 방법](../CONTRIBUTING.ko.md)을 참고하세요.
