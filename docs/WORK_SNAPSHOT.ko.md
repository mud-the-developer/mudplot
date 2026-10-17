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
- 잘못된 행 타입/너비 불일치의 값 왜곡, Windows 읽기 전용 staging 누수, Rust 예약-key 재해석,
  생략된 spec version 처리 차이·범주 x 결측의 가짜 label 표시를 수정했습니다. Rust 거부
  응답 header와 선언 body 크기의 선행 거부도 보강했습니다. Query로 만든 cursor만
  정리하며 borrowed cursor/connection/transaction은 보존합니다. Python framing을 명시하고
  Rust는 모든 handler 전 unknown-size body도 검사합니다. NumPy/Polars fine-unit 날짜
  정밀도와 Rust smoke CI의 선택 의존성도 보강했습니다. 상세 finding/제한은 대장에 있습니다.

## 검증과 리뷰 상태

- 최신 이력 대상 **199통과**, 전체 Python browser **32통과** 및 실제 Rust HTTP/
  browser도 통과했습니다. 최소 history-only **20통과/경고13**은 과거354case의 반복이
  아닙니다. 이전1116/27·optional244는 과거의 겹치는 범위이지 새 전체 앱 검증은 아닙니다.
- Browser **31통과**와 native Rust **15통과/helper1ignored**는 이전11차 결과이며
  새 count가 아닙니다. 이번12차 격리 all-extra Rust smoke는 로컬 통과했습니다.
  Form/JSON/chunked39순차 body case와 실제 서버 PID 수명 peak를 관찰했지만 native
  렌더 자식/전체 앱 CPU·메모리·동시 부하 상한은 아닙니다. Compiler **1.99.0**이지
  MSRV 검증이 아니며 이전 Windows transport 중단 원인이 해결됐다는 주장은 하지 않습니다.
- Ruff/Pyright·생성 계약 sync·clean sdist→wheel 검사 통과.
- [휴대 가능한 검증 요약](review_evidence/verification_receipts.json)에 경로를 제외한
  결과·환경/소스 지문·원본 log hash를 보존했습니다. Raw log는 로컬에 있으며 이 요약은
  새 실행 결과가 아닙니다.
- [Adapter 요약](review_evidence/data_shape_verification.json)과 최신
  [결측/상태 검증 요약](review_evidence/missing_state_verification.json)에 소스 지문·명령 범위·
  결과·커서 표를 보존했습니다.
- [최신 editor 경계 요약](review_evidence/editor_boundary_verification.json)에 최종13개
  성공 명령·공통 상태 해시를 보존하고 이전 실패/제한도 별도 기록했습니다.
- [Codec/경로 요약](review_evidence/codec_path_verification.json)에24모델/272필드·
  typed Python→Rust→Python 왕복과 Windows 별도 venv child argv를 경로 제거해 보존합니다.
  후속 Linux/Windows 실제 성공 근거는14차에 있습니다.
- [Table/SQL 요약](review_evidence/table_sql_verification.json)에 실제 optional 버전·
  형식/소유권 범위·격리 venv 정리를 기록했습니다. 프로젝트 패키지/lock은 유지합니다.
- [Body 경계 요약](review_evidence/body_boundary_verification.json)에 framing/크기/status/
  상태 보존과 올바른 worker-PID 메모리 관찰을 보존합니다.
- [Temporal/CI 요약](review_evidence/temporal_ci_verification.json)에 정밀도/CI 의존성 수정을
  기록했습니다. 359277c의 Python jobs는 성공했지만 Linux Rust smoke 실패·Windows
  취소였으며 수정 후 원격 재통과는 아직 관찰하지 않았습니다.
- [Scalar/계측 요약](review_evidence/scalar_provenance_verification.json)에 미지원 값의
  명시적 거부와 가려지지 않는 recorder를 기록합니다. Linux914a402 smoke는 통과 후
  provenance에서 실패했으며 후속781f3f5의 양 OS Rust jobs는 성공했습니다.
- [이력 정책 요약](review_evidence/history_policy_verification.json)에 문서/no-op/replay/UI와
  원격781f3f5 양 OS Rust·Python3.12 성공을 기록했습니다. Python3.10 취소로 전체는
  cancelled이며 이를 후속 UI 수정의 원격 통과로 소급하지 않습니다.
- [150-ID 리뷰 대장](REVIEW_CHECKLIST_STATUS.md): **PASS 34 / RUNNING 12 / OPEN 104**.
  미검증 항목을 통과로 취급하지 않습니다.

이전 기능/최소환경/브라우저 결과는 각자의 범위이며 후속 변경 이전 결과입니다.
이를 현재 전체 작업 트리의 검증으로 확대하지 않습니다. 전체 Python/최소환경 matrix,
Rust MSRV·Linux/TeX·의존성 보안 감사·성능·릴리스 provenance gate는 미완료/보류입니다.

지원 범위와 제한은 [구현 계획](V1_1_PLAN.ko.md), [기능표](FEATURE_COVERAGE.ko.md),
[Unreleased 변경 이력](../CHANGELOG.md)을 확인하세요.
