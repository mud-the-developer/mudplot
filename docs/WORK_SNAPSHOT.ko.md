# Unreleased 작업 스냅샷

*[English](WORK_SNAPSHOT.md)*

현재 로컬 구현·기존 작업 트리 변경·예제·생성 계약·리뷰 작업을 함께 정리한
스냅샷입니다. **릴리스가 아니며** Matplotlib/Seaborn 전체 동등성이나 모든 변경이
한 세션의 작업이라는 주장이 아닙니다. Package/editor **1.0.0**, spec **0.1**은 유지합니다.

## 포함한 작업

- 원자료 통계·가중치/단위·범주/분포 옵션·scatter/line semantic 확장과 기존 기본값 호환.
- Facet/joint/numeric pair 구성 및 histogram/KDE grid 부분 구현.
- Typed heatmap·선택 고급 회귀/residual effect·원자료/metadata를 정렬하는 clustermap.
- Python/Rust editor·브라우저 import/edit·한영 가이드·schema/capability/reference와
  실행 가능한 시각 예제 갱신.
- 행 너비 불일치의 값 잘림, Windows 읽기 전용 staging 누수, Rust 예약-key 재해석,
  생략된 spec version 처리 차이 수정. 상세 finding은 증거 대장에 있습니다.

## 검증과 리뷰 상태

- 최신 기록된 Python 대상 검사: **597 통과, Windows 조건 2 skip**.
- Rust native **14 통과, 의도한 helper 1 ignored**; 실제 HTTP/브라우저 smoke·
  Clippy/fmt 통과. Compiler **1.99.0** 결과이며 MSRV 결과가 아닙니다.
- Ruff/Pyright·생성 계약 sync·clean sdist→wheel 검사 통과.
- [휴대 가능한 검증 요약](review_evidence/verification_receipts.json)에 경로를 제외한
  결과·환경/소스 지문·원본 log hash를 보존했습니다. Raw log는 로컬에 있으며 이 요약은
  새 실행 결과가 아닙니다.
- [150-ID 리뷰 대장](REVIEW_CHECKLIST_STATUS.md): **PASS 11 / RUNNING 14 / OPEN 125**.
  미검증 항목을 통과로 취급하지 않습니다.

이전 기능/최소환경/브라우저 결과는 각자의 범위이며 후속 변경 이전 결과입니다.
이를 현재 전체 작업 트리의 검증으로 확대하지 않습니다. 전체 Python/최소환경 matrix,
Rust MSRV·Linux/TeX·의존성 보안 감사·성능·릴리스 provenance gate는 미완료/보류입니다.

지원 범위와 제한은 [구현 계획](V1_1_PLAN.ko.md), [기능표](FEATURE_COVERAGE.ko.md),
[Unreleased 변경 이력](../CHANGELOG.md)을 확인하세요.
