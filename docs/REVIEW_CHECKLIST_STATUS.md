# 2026-10-16 체크리스트 반영·증거 대장

원문: [상세 체크리스트](../mudplot_review_checklist_detailed_2026-10-16.md)

작업 스냅샷: [한글](WORK_SNAPSHOT.ko.md) · [English](WORK_SNAPSHOT.md).
임시 경로가 사라져도 [경로 제거 검증 요약](review_evidence/verification_receipts.json)의
실행 범위·결과·환경/소스 지문·원본 log hash를 확인할 수 있습니다. Raw log 복제나
새 전체 검증 결과를 뜻하지 않습니다.

**150개 검증 항목이며 결함 개수/제품 안정성 확률이 아닙니다.** 원문 체크박스는 보존하고 이 대장에서 실행 상태를 관리합니다.

- 기준 HEAD: `c4f40ab22660129ad4e35c63d1f66feb62e2dd99` (원문과 일치).
- 적용 범위: 기존 로컬 변경/새 파일 포함 작업 트리. clean main 재현으로 주장하지 않습니다.
- 날짜/환경: 실제 environment.json 참조; Windows 11, Python3.12.15, NumPy2.5.2, Matplotlib3.11.1.
- 1차 명령: `uv run --no-sync python -m pytest -q tests/test_review_state_contracts.py tests/test_review_output_contracts.py tests/test_reducer.py tests/test_spec_roundtrip.py tests/test_json_schema_compat.py tests/test_schema_export.py tests/test_no_deps.py tests/test_stabilization.py tests/test_cli_apply.py tests/test_cli_migrate.py --junitxml=<evidence>/contracts.xml`.
- 실제 결과: **127 passed, 2 Windows-only skips, exit 0**, 25.33s. skip: symlink privilege/POSIX mode bits.
- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-2026-10-16-88esbi7s` (임시 경로; 보관이 필요하면 별도 복사).
- 파일: environment.json(버전/원문 SHA256/변경 파일 SHA256), git-status.txt, tracked-diff.patch, contracts.log, contracts.xml, receipt.json.
- 담당: coding assistant; 관련 PR/tag/배포 없음. 기존 변경 전체를 이번 작업으로 귀속하지 않습니다.

## 71차 — 독립상태oracle·축소fixture·격리선정mutant검사

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-state-mutations-xvltk6yv`와
  [상태공간/선정mutant/checkout무변경](review_evidence/state_mutation_verification.json),
  `tests/fixtures/state_machine_regressions.json`의검토한두trace를보존합니다.
- 고정seed외에8event/depth1..4의4680trace와64/128checkpointprefix의3eventsuffix1024trace,
  총5704trace/21128generatedevent검사를수행했습니다. 독립title/size/panel/history/futureoracle가
  전체spec/JSONroundtrip/실패negativeindex무전이/반환·listener snapshot외부수정격리를확인합니다.
  같은reducer를expectedstate계산기로재사용하지않고기존768-actionseed검사도유지했습니다.
- Shrinker는한event삭제로더이상실패를유지할수없는deletion-minimal이지전역최소/Hypothesis전체
  shrink보장은아닙니다. Controlledstaleredo의A→undo→B→redo와실제isolatedsource mutant가찾은
  A→undo→A→redo를고정fixture로검토해기록하고정상Store에서다시통과시켰습니다.
- 실제checkout은patch하지않고runtime/dashboard/tests소유copy의import경로를assert했습니다.
  원copy의25baseline통과후secondary→primary축/그룹dtype추론/duplicate-last-wins/실패시이전target삭제/
  redoclear누락의5선정mutant를넣어23의도test실패로모두검출했습니다. Groupmutant는4param중2만
  실패하므로전체linecoverage/모든입력검출률이라고하지않습니다. Collection/import오류/skip은kill로세지않았습니다.
- 축text소속누락/원group행혼합·분리/duplicate미거절/이전파일소실/최소redosignal의실패가맞고
  원runtime3파일SHA는실험전후같았습니다. Reset/stash/checkout원복명령으로원work를덮지않았습니다.
  실험뒤추가한fixture/test는의도된검토추가이며실험당시옛지문과현재지문을구별합니다.
- 새9·관련52통과·floor9/3216deselected/경고13·isolated5×baseline/mutant대비·양platformtype/
  Ruff265/생성계약/packaging9명령exit0·변경2경로activeLSPclean입니다. 13은모두3종Pyparsing이며
  oracle의잘못된None-title가정을실제문자열default/typedtuple로수정했지Any/cast/ignore로숨기지않았습니다.
- CI-03/05는이grammar/depth/선정계약범위PASS입니다. 제품runtime/새dependency/lock/version/tag/
  publish는변경하지않고ce717CI39212306093의양Rust성공/3Python진행을보호해testunit은로컬보존합니다.
  모든action조합/일반mutationcoverage/새현재소스전체CI를완료했다고하지않으며loop1/gates는유지합니다.

## 70차 — API/Python/Rust비용과대형지원범위·CI명령검사보존

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-e2e-costs-azds8gdv`와
  [동일state/pixel/cold-warm/component](review_evidence/e2e_performance_verification.json),
  [성능안내](PERFORMANCE.ko.md)/[English](PERFORMANCE.md)를 보존합니다.
- 같은4×3inch/100DPIrawline3columns/1k·10k행/제목action5개를directAPI·Pythonform·Rusttitleform에
  적용했습니다. 최종spec와previewpixels가같고invalidlayout뒤validaction도state/cache를보존합니다.
  WarmAPI(publicatomicPNGsave·close·read)는median530/553ms,PythonHTTP+PNGfetch561/597ms,
  Rust4215/4431ms였습니다. 표본5의nearestp95는관찰max이지안정적tail/SLA가아닙니다.
- 100회JSONencode/decode/reduce/snapshot/validation,3회freshCLIcontext를별도로측정했습니다.
  Rust는정상action마다apply+renderPythonchild2개이며HTML은1k/10k203KB/1.82MB(Python25KB)
  였습니다. APIfilesystem/HTTPbuffer/DOMpaint·colddefault준비/첫open·중첩component를섞어
  합산하지않고privatefontcache/설정인터프리터/관찰poll지연을기록했습니다. 추정/ui_action404첫시도는
  폐기하고실제/control/title로새cold디렉터리에서완료한결과만사용했습니다.
- 이미측정·검증한단일checkpoint의replay/memory/state/listener/noop/실패계약sourceSHA는현재와같습니다.
  싼rawvalidation을삭제할이유가없고streaming/immutable/zero-copy필수주장을하지않았습니다.
  큰100k×긴history의budget미완료는undo·redo=null로남기며domain명시집계는원본/count와
  달라진관측의미를보존합니다. 후속data/spec분리는실제병목이증명됐을때의설계경계입니다.
- 기준21dCI39207855660은3.10의기존literal `run: uv run pytest...` assertion1개로실패했습니다.
  3983case/필수실제browser·PGF·Tectonic은통과했고strictgate가전체failure를거절한것이맞습니다.
  YAMLfolded명령/JUnit추가를step단위로읽도록기존test만고쳤고60분/fullsuite/durations25/JUnit/
  selector금지는유지합니다. 4CI효과tests도minimum에포함했으며gate/runtime/workflow를느슨하게하지않았습니다.
- 새집계문서2·관련79통과·floor15/3201deselected/경고13·1k/10kE2E/100component/3CLI/5warm·
  양platformtype/Ruff264/생성계약/packaging9명령exit0·변경3경로activeLSPclean입니다.
  13은모두3종Pyparsing이고snapshot/성능source/실패CIlogSHA를분리합니다. PERF-05/07/08은
  이범위PASS이며긴native세션PERF-04/전체CPU·memory보장으로올리지않습니다.
- 기준21dCI는3.10실패/3.12cancelled/최소환경·양Rust성공으로종료됐지성공으로변경하지않습니다.
  문서/CItest수정만게시해새전체CI를받고runtime/버전/의존성/lock/tag/배포·loop1경계는유지합니다.

## 69차 — 필수browser/TeX실행gate와matrix/순서증거

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-ci-paths-drubgwvw`와
  [도구유무/실제JUnit/병렬matrix](review_evidence/ci_path_matrix_verification.json)을 보존합니다.
- 선택pytest는도구가없으면정상skip/exit0일수있습니다. Privatechild만실제Playwrightlaunch를
  없는exe로유도/TeX탐색을숨긴경우3skip/pytest0였고새requiredgate는exit1로거절했습니다.
  바이너리를실제제거하거나가짜도구버전을성공으로보지않았습니다. 도구present는browserlegend/
  nativePGF/Tectonic/pdflatex+BibTeX/LuaLaTeX+BibTeX/LuaLaTeX+biber6개실행통과입니다.
- `check_required_test_paths.py`는ci3/minimum2/tex3/release6의고정JUnitidentity가한번passed여야
  합니다. Missing/skip/xfail/fail/중복/없거나깨진report는실패하고무관한optional skip은허용합니다.
  Reader는64MiB/UTF-8(BOM허용)/NUL·DTD·entity금지이며XML진단은이경계와회귀로고쳤습니다.
  새로운dependency/Any/ignore로숨기지않고activeLSP3경로clean을확인했습니다.
- Workflow는JUnit과실패사유를always검사/보관하되실패job을성공으로복구하지않습니다.
  MatrixPython/sourceSHA이름으로report/UVcache접미사를분리했고nightly/releasecacheoff와
  permissions/events/need-build/publishguard는그대로입니다. 기존pinnedartifactaction만재사용했습니다.
  Pinnedsetup-uvmetadata의cacheinput을검사했지thirdparty전체구현/서명provenance인증은아닙니다.
- 별도process의원순서/seed52673변경순서는같은41ID/다른order로각41pass/0skip였고temp/font/
  report가분리됐습니다. 임의순서/동일Storethread/Mpl병렬안전전체를보장하지않습니다. Monitor3/4의
  0line launchererror는결과가아니며나중정상bash실험receipt만계산했습니다.
- 새20/관련37통과·floor20/3190deselected/경고13·actual6/4profilegate0·2×41pass·품질10명령exit0,
  Ruff263/양platformtype/생성계약/packaging가맞습니다. 13은모두3종Pyparsing,YAML은0error와
  기존7warning(documentstart/GHAon/comment)을구분합니다. 새검사script/TESTS추가외lock변경없습니다.
- 실제d221CI39201840394ALL5SUCCESS를확인했습니다. 3.12는3956pass/46skip뒤optional243pass,
  floor는3145pass/37skip이며원인/구버전nightly3pass+Tectonic1skip을구분합니다. 이로이전046/
  checkpoint전체를확인했지만새JUnitgate가그때실행됐다고소급하지않습니다.
- CI-02/06은이source/실험범위PASS입니다. 대기문서+CI변화를함께게시해새전체CI를받고CI-01/
  공급망/릴리스gates·버전/의존성/lock/tag/배포·loop1은유지합니다. JUnit은악성test방어/출처서명이아닙니다.

## 68차 — 문서정합/API변화/증거수준의작성자검토

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-doc-review-hdbzn_ev`와
  [문서/API/예제receipt](review_evidence/documentation_review_verification.json),
  [잠정작성자판단](REVIEW_DECISION.md)을 보존합니다. 독립reviewer/최종release승인이아닙니다.
- 한글/영문README의무조건흑백식별문구를finitecycle/실제크기조건으로맞추고현재checkout의
  256panel/cell·1024layer·bivariate512·owned40Mpixel/Unreleased/purecheckpoint범위를같이
  기록했습니다. Render/save의성공반환Figure는caller소유라는실제API계약을유지하며builder와
  provenance예시의반환Figure를명시close했습니다. Recipe누수3개→0회귀로확인했고생산API를
  편집기/CLI내부Figureclose와혼동하지않습니다.
- 원문기준c4f40a와현재AST의rootexports41→52/Plot70→84/action32→36은추가이며삭제는없습니다.
  기존modelannotation/default는유지되고optional y/kwarg추가와scatter의**style→**appearance/
  전용semanticstyle역할을분리했습니다. CLI7명령/6flag는같습니다. 이를전행동무변화라고하지않고
  securityresourcebound의기존positive값수용축소·진단문구개선을명시적예외로기록했습니다.
- Productionrepro/fixed·문서/예제오류·CI/test약점·성능한계·미실행제안을다른증거수준으로
  분리했습니다. 숫자qualityscore/안정성확률/사람AT시험을새로붙이지않고gate표는현재BLOCKED를
  남깁니다. DOC-04/05/06의최종평가/재평가/최종인계는OPEN그대로입니다.
- 새doccontract8·관련63통과·floorREADME/recipe9통과/3181deselected/경고13·relativefile링크
  198개실재·양platformtype/Ruff261/생성계약/packaging9명령exit0·변경3경로activeLSPclean입니다.
  13은모두3종Pyparsing이며link검사는anchor/외부URL전체crawl이아닙니다. Source-onlyAST비교라
  옛runtime을실행하거나signature만으로모든조합호환성을추정하지않았습니다.
- DOC-01/02/03은이source/evidence범위PASS입니다. Runtime/새FIND/버전/의존성/lock/tag/배포를
  바꾸지않고기준d221CI39201840394의양Rust성공/3Python진행을보호해문서unit은로컬보존합니다.
  Publish/독립signoff권한을보고서로새로만들지않으며loop1/남은gates를유지합니다.

## 67차 — gesture경계·단일checkpoint·선택manifest

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-history-provenance-ibkva6i9`와
  [전후profile/gesture/memory](review_evidence/history_improvement_verification.json),
  [manifest예시](OUTPUT_PROVENANCE.md)/[합성결과](review_evidence/provenance_manifest_example.json)를 보존합니다.
- 실제browser두drag는각100move중요청0/release1commit이었고중간title편집을합치지않아
  history는SetLayerAt/SetTitle/SetLayerAt3개였습니다. Undo는gesture/독립edit경계를정확히
  복원합니다. Focus-onlyclick은dispatch가없어0event이지core의명시no-opevent를없앤것이아닙니다.
  새corecoalescer/Esc-cancelAPI를넣지않고기존keyboardburst검사도재실행했습니다.
- 기존9caseprofile의1k행/1000actionsundo약405→17ms,10k행/256actions의cached/control은
  약219/860ms이며추가tracedretainedPythonbytes약51KB/280KB를측정했습니다. Defaultpure
  reducer만이전64경계의내부state한개를보관하며replay전deepcopy/초기fallback/branch폐기를
  합니다. Customreducer는fullreplay/호출수유지,모든history/redo/noop/listener실패후commit/
  SetData/반환snapshot의의미를검사했습니다. 한cache도fullspec크기비용은있고hardRAM이아닙니다.
- 중단된큰profile은target미도달/undo·redo=null로남기고0ms라고하지않습니다. 초기private
  prototype는빈applysuffix에cache를직접주면alias가생겨copy를명시했으며새Store_replay도
  같은방어를합니다. Prototype전체listener/branchAPI가제품구현과같다고가정하지않았습니다.
- Provenancerecipe는새directory에만canonicalspec/data/env/primaryfont/outputhash를별도JSON으로
  남기고image의timestamp/history를변경하지않습니다. Image3형식재저장bytes동일/metadata환경
  whitelist/기존directory거절/원output불변이맞습니다. Hash는익명화가아니며fallback/TeX/전체
  ambient환경을잠그지않습니다. 새save옵션/mandatorysidecar는없고합성데이터만공유합니다.
- 새core9/recipe1/browser1·관련201통과·실제browser4통과/29deselected(no skip)·floor10통과/
  3172deselected/경고13·9profilecase/2memory비교·양platformtype/Ruff260/schema/packaging11명령
  exit0·변경5경로activeLSPclean입니다. 13은모두3종Pyparsing입니다. 직접Storetypedimport/helper
  annotation과현재정의로초기staleattribute진단을확인했고Any/getattr/ignore는없습니다.
- HIST-07/08/OUT-10은이관찰/구현/recipe범위에서PASS입니다. 기준06fCI39196761559는5job모두
  성공해이전044/045전체검증을확인했습니다. 대기layer+checkpoint효과를함께게시해새전체CI를
  받으며버전/의존성/lock/tag/배포·loop1/남은gates경계는유지합니다.

## 66차 — 총layer의decode/add/facet/joint확장상한

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-layer-budget-hv8c7vza`와
  [before/after5·copy/decode·HTTP6](review_evidence/layer_budget_verification.json)을 보존합니다.
- **FIND-046:** 명시color는자동palette계산을건너뛰므로후보720한도가layer방어가아닙니다.
  작은비교입력의256/512/1024coloredscatter는실제render되고큰raw배열은기존시험wallbudget에
  걸렸습니다. 공통MAX_FIGURE_LAYERS1024를Figure전체합계로제한해개별rawLayerdecode/
  새AddLayercopy/facettemplate·jointsource복제전에검사합니다. DirectSpec도validation이조기거절합니다.
- SinglePanel/다중Panel합계raw와standalonePaneldecode를모두검사하고1024경계/AddLayer/
  facet·joint의정상복제와입력은유지합니다. Pairgrid는기존최대64개one-layercells이므로쓸데없는
  guard를더하지않았습니다. 초기12회귀8실패/4정상이최종12통과했으며oldexactcapabilitytest도
  새max_layersmetadata를명시해같은boundsassert를유지했습니다.
- 명시color1024fixture약217MBpeakRSS/3.2sworker,초과decode는ValueError로바뀌었습니다.
  실제Python/RustHTTP6사례의AddLayer/facet/open거절은committedspec/cache를보존합니다.
  RawJSONparsecost가count검사보다먼저일어나는점과모든artist/data/CPU한도보장은구분합니다.
- 새12·관련591통과·floor12통과/3160deselected/경고13·before/after5/HTTP6·양platformtype/
  Ruff257/생성계약/packaging10명령exit0·변경9경로activeLSPclean입니다. 13은모두3종Pyparsing이며
  새dependency/specversion/option/sandbox/입력clamp는없습니다.
- SEC-04는여전히RUNNING입니다. Text/다른algorithm/CPU/전체memory정책은남고privateJob의
  budgetstop을제품성공으로세지않습니다. 기준06fCI39196761559의양Rust성공/3Python진행을
  보호해layer효과는로컬보존하며새전체CI/버전/의존성/lock/tag/배포·loop1경계는유지합니다.

## 65차 — source보존과effectpixelbudget의분리

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-effect-budget-keyuqfhr`와
  [before/after7·tight/atomic·HTTP8](review_evidence/effect_budget_verification.json)을 보존합니다.
- **FIND-045:** valid한큰DPI/작은spec도정확한render/save의Agg/layout/SVGimage작업에서
  privateJobmemorybudget에걸렸습니다. Spec/DPIvalidator로막으면안전한cappedpreview까지
  깨지므로공통_check_render_budget을effect전에만두었습니다. 40millionpixel상한을Figure생성전,
  실제backenddpi/outputdpi/padding포함tightbbox에서검사하고원DPI/size를clamp하지않습니다.
- Rawspec은여전히load/validate되고preview는2000²copy입니다. 정확한SVG/PDF도현재pipeline의
  DPI기반canvaswork에따라초과ValueError입니다. Allocation/save-spy9baseline는안전하게실패했고
  최종새18회귀가경계/floatoverflow/preview/source/이전파일/staging/Figure소유권을검사했습니다.
- Privateguard의6000²/6320²PNG는완료됐고초과/큰vectorimage작업은allocationbudget중단에서
  초기ValueError(~65MBpeakRSS)로바뀌었습니다. Python/RustHTTP8outcome은preview/edit/source를
  보존하고거절400HTML/500plain을정상SVG로위장하지않으며명시낮은DPI제출뒤200으로회복합니다.
- 관련315통과/Windows4symlinkskip·floor18통과/3142deselected/경고13·측정before/after7/
  HTTP8·양platformtype/Ruff256/생성계약/packaging10명령exit0·변경5경로activeLSPclean입니다.
  Helper구현전staleLSPevent는현재정의/activeallservers/cache/Pyright0으로확인했고codeignore/
  Any/getattr를넣지않았습니다. QA뒤comment/docstring만바꾼것은기록SHA/비문서AST동일확인과18재통과로분리했습니다.
- SEC-04는여전히RUNNING이며다른layer/text/CPU/총memory정책이남습니다. 이pixelarea상한을
  hardRAM/time/sandbox로부르지않습니다. 기준2a96CI39191652835의5job모두성공으로이전041/042/
  043및Linux확대/focus/fullnativebrowser검증을확인했습니다. 대기구조+effect를함께게시해새소스
  전체CI를받고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 64차 — Panel/layout/decode확장의사전상한

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-structure-budget-eg46hd7n`와
  [before11/after13자원·decode/constructor·HTTP](review_evidence/structure_expansion_verification.json)을 보존합니다.
- **FIND-044:** 작은index/layout/rawpanelarray가대량PanelSpec/native구조로확장됐습니다.
  공통MAX_FIGURE_PANELS256을두어_ensure_panel이생성전에검사하고AddPanel/SetLayout도
  그경로를쓰게했습니다. Rawpanels배열은개별Paneldecode전,직접구성spec은validation에서
  panel/layoutcell초과를조기거절합니다. 초기11회귀8실패/3정상이최종11통과했습니다.
- index99→100panels,255→256panels/마지막AddPanel/16×16layout은원값/입력snapshot을
  보존합니다. 초과는clamp/삭제/새option이아닌ValueError이며비정수/bool/음수의기존거절도
  유지합니다. 최대256cap은semanticresource범위로새serializedfield/specversion을만들지않았습니다.
- PrivateWinJob에서64/128/256실제panels가완료되고256fixture는약212MBpeakRSS/5.1sworker
  였습니다. 초과decode/action/layout은약65MB에서거절되고Native/PythonHTTP6사례의
  committedspec/PNG는불변입니다. 모든max-datafigure/time/메모리보장으로확대하지않습니다.
- 새11·관련489통과/Windows2skip·floor11통과/3131deselected/경고13·측정11→13/HTTP6·
  양platformtype/Ruff255/계약/packaging10명령exit0·변경6경로activeLSPclean입니다.
  13은모두3종Pyparsing이고이전privateworker는기록SHA그대로복원한뒤새증거folder로분리했습니다.
- SEC-04는여전히RUNNING입니다. Exactexport/rasterization·다른layer/text/입력처리의자원
  정책이남아제품에hardRAM/CPU/sandbox가설치됐다고하지않습니다. 기준2a96CI39191652835의
  양Rust/min성공/양Python진행을보호해구조효과는로컬보존하며새전체CI/버전/의존성/lock/
  tag/배포·loop1의경계는유지합니다.

## 63차 — 제한process의자원증폭측정과bivariate상한

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-resource-guard-bsx7rf8a`와
  [sanitized RSS/commit/time·before/after·HTTP](review_evidence/resource_amplification_verification.json)을 보존합니다.
  미패치구조/export의구체payload와probe소스는private이며공개요약에는종료/크기/hash만남깁니다.
- WindowsJob을먼저설정하고CREATE_SUSPENDED child를assign한뒤에만resume했습니다.
  UVlauncher가한child제한에막힌첫자체검사는큰입력전중단됐고명시적으로같은baseCPython3.12.15+
  현venvsite-packages를선택했습니다. 64MiB memory자체검사와CPU/WALL종료검사를기록하며
  기본512MiB는processcommit한도이지RSS한도가아닙니다. CPU검사/종료는coarse이며setup/
  termination오버헤드를뺀순간hard-time보장으로해석하지않습니다. 이는제품에설치한guard가아닙니다.
- **FIND-043:** 작은JSON의legacyhist2d/hexbin무제한positivegrid가nativequadraticallocation까지
  갔습니다. 공통validator에축당512bins/513edges·hexgridsize512를두어초기11회귀7실패/4정상에서
  최종11통과했습니다. 정상512는원값대로끝나고초과는clamp가아닌validation거절입니다.
  Native/PythonHTTP4거절은현재spec/cache를보존하고caps를재생성했습니다. 1D10000bin은유지합니다.
- Before17/after18제한child측정에서큰요청DPI/canvaspreview는실제2000pixel이내였고
  bivariate초과는memorybudget중단에서validation거절(~65MBpeakRSS)로바뀌었습니다.
  다른구조확장/정확한raster·vector-image export는여전히시험budget에걸렸으므로SEC-04를
  OPEN→RUNNING으로만변경합니다. Layer예제의palette거절도보편layercountcap이라고하지않습니다.
- 관련263통과·floor11통과/3120deselected/경고13·HTTP4·측정18기록·양platformtype/Ruff254/
  schema/packaging10명령exit0입니다. 측정완료exit0이모든제품case의성공이라는뜻은아닙니다.
  13은전부3종Pyparsing이며새dependency/specversion/전역budgetframework는없습니다.
- 기준cb2CI39187999070은3.12의확대RedoLocatorclick pointer-interception1실패/3.10cancelled입니다.
  이전focuswait/data검사는통과했고[pinch UI활성화근거](review_evidence/browser_pinch_activation_verification.json)는
  같은Undo/Redo버튼을Enter로활성화해정확한state검사를유지합니다. Pointerdrag는그대로이며
  forceclick/직접Store호출이아닙니다. 관련로컬4통과이지모든mouse-toolbar/nativezoom보장은아닙니다.
- SEC-04와CI-01은진행중이며구조/export추가정책및새Linux전체CI가필요합니다. 버전/의존성/
  lock/tag/배포·loop1은유지하고큰작업을무제한으로실행하거나실패한CI를성공으로세지않습니다.

## 62차 — 공유static/license와matchingcheckout경계

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-editor-assets-kff9yi0o`와
  [자산hash/라이선스·4runtime·미확인smoke](review_evidence/editor_asset_verification.json)을 보존합니다.
- 추적htmx는dashboard/static의JS/0BSDlicense2경로뿐이며Rustinclude_bytes는같은JS를
  씁니다. 실제Python/RustHTTP및nativeChromiumwindow.htmx1.9.12의응답SHA가원본과같고
  embeddeddefaultspec/currentgeneratedcaps/Python·Rust·Cargo.lockmetadata도일치합니다.
- 현Pythoncontrolledruntime4종에서current/compatiblelabel9.9.9-probe는정상startup/action,
  spec9.9-probe/missingthemescapability는실제bridge오류로startup거절됐습니다. Runtimepackage
  labelhandshake는원래없으며이를새guard/field로추가하지않았습니다. 별도releasepreflight의
  Pythonmetadata불일치fixture는project/Rust/lock차이를설명하며수용이모든과거배포판호환보장은아닙니다.
- 표준rust_editor_smoke_test.py--browser는전체QA480s예산중진행하다outertimeout으로
  exitreceipt없이끝났습니다. 빈native.log/후속ownedprocess없음을기록했고통과/제품assertion
  실패로세지않습니다. 그뒤RUST-07전용실제browserasset로드/hash를별도로수행했지전체smoke를
  작은검사로통과치환하지않았습니다. WholeCI/gate결과와도구분합니다.
- 새pure2·관련176통과·실제nativefocusedbrowser1·4controlledruntime·floor2통과/
  3118deselected/경고13·양platformtype/Ruff253/생성계약/packaging9명령exit0·새test/minrunner
  activeLSPclean입니다. 13은모두3종Pyparsing이며native전용sitecustomize와floorplugin경로를
  분리해다른환경/설치파일에개입하지않습니다.
- RUST-07은현재matching-source/assets/controlledmismatch범위PASS입니다. Runtime/FIND추가는
  없습니다. 기준489aCI39183500953은3.10의DPR3casefocus즉시assert실패/3.12cancelled로끝나
  성공이아닙니다. [focus동기화근거](review_evidence/browser_focus_sync_verification.json)에
  실제joblog와정확한postcondition5초wait를보존했습니다. Assertion/data조건을제거하지않고
  HTMXrequestAnimationFrame복원을기다리며로컬관련4case통과/새LinuxCI필요를구분합니다.
  대기HTML의미/자산/test동기화를함께게시하고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 61차 — keyboard경로와alert/current상태의미

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-keyboard-access-w5uvdwsx`와
  [Tab순서·pointer0·error/handle/nav검토](review_evidence/keyboard_access_verification.json)을 보존합니다.
- **FIND-042:** 보이는오류문자에는alert의미가없고활성Editor/Docs는CSSclass뿐이었습니다.
  초기pure3회귀가전부실패했고오류에role=alert/현재link에만aria-current=page를덧붙였습니다.
  Escaping/CSS표시/폼action/navigationhandler/spec/state/focus정책은바꾸지않았습니다.
- 실제Chromium에서Tab/Enter/Control+A/typing/화살표/Shift+ArrowLeft만으로panel2→title→
  AdvancedJSON오류alert→수정성공→titlehandle보통/큰이동→Docs/Editor왕복을검사했습니다.
  직접element.focus()/mouseclick없이pointerdown0,현재panelaria-pressed와control의label연결,
  handle2pxoutline/HTMX후focus유지/오류해제/원panel불변과pageJS오류0이맞습니다.
- Codingassistant의DOM/CSS/source검토와실제키보드자동화기록이지독립적인사람의AT사용성
  연구가아닙니다. Forward-onlyTab은77/78/86step인구간도기록했으며새shortcut/rovingfocus를
  만들거나Rust모든control/OSfilepicker/WCAG보편인증으로확대하지않았습니다.
- 새pure3/browser1·관련169통과·실제browser6통과/27deselected(no skip)·floor3통과/
  3115deselected/경고13·양platformtype/Ruff252/계약/packaging9명령exit0·변경4경로activeLSP
  clean입니다. 13은전부3종Pyparsing이고pure만floorroster에추가해Playwright의존성은늘지않았습니다.
  추측한to_jsonfallback/Optionalpositionstub/JS문자열길이는검사전고쳤고Any/cast/ignore는없습니다.
- EDIT-08은현재Python지원keyboard/의미corpus에서PASS로EDIT01..09검토를마쳤지만완전한
  접근성인증은아닙니다. 기준489aCI39183500953의양Rust성공/3Python진행을보호해새HTML효과는
  로컬보존하며이전CI를소급하지않습니다. 버전/의존성/lock/tag/배포·loop1은유지합니다.

## 60차 — field오류위치와실제machine응답계약

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-machine-contracts-5kqxu18l`와
  [before/after26응답·route/CLI/agent표](review_evidence/machine_error_verification.json)을 보존합니다.
- **FIND-041:** width/height잘못된string의CLI설명이둘다expectednumbergotstr로동일해
  field가사라졌고Rustagent도같은설명을받았습니다. 초기8회귀5실패/3정상union통과를확인하고
  공통_from_dictdataclassfield경계에서Class.field만덧붙였습니다. TypeError/ValueError/원인을
  유지해union의TypeErrorfallback을바꾸지않으며nestedchain/input불변/엄격ValueError도최종9회귀가맞습니다.
- 실제CLIapply는결과JSONfile/stdout빈값/exit0·1/stderrprogress-error,capabilities는stdoutJSON입니다.
  PythonUIrawform은정상nonHX303redirect/HX오류200HTML이지JSONRPC가아닙니다. GETspec은JSON,
  PNG/PDF/SVG는실제media입니다. Source기반route를써서정상/오류envelope를가정하지않았습니다.
- 현소스로빌드한실제WindowsRustHTTP는action200JSONspec/400badfield·negativepanel/415media/
  422syntax·UTF8·duplicateJSONerror만반환하고실패spec/cache는불변입니다. Native전용private
  sitecustomize로SVGchild만exit7시키면500text/plain이지성공vector가아니며정상action/export로
  회복했습니다. 위조response가아니고다른command는실제Python으로위임하며server는종료/reap했습니다.
- 허용진단은공개field/type/JSONline-column이며검사한numericcanary는echo하지않습니다.
  이것이기존모든union/value/backend오류의보편redactor는아닙니다. 양수panel99는자동확장
  계약이라초기QA가정을바로잡아음수-1로대조했지새panel한도/JSONRPC를만들지않았습니다.
- 새pure9/실제26응답·관련386통과/Windows2skip·실제browser3통과/30deselected(no skip)·
  floor9통과/3106deselected/경고13·양platformtype/Ruff250/생성계약/packaging10명령exit0·변경
  3경로activeLSPclean입니다. Floor13은전부3종Pyparsing이며연결suite의2UserWarning은
  pointplot의singleton통계interval생략으로별도분류하고숨기지않습니다.
- EDIT-07/09는이actualUI/CLI/nativeHTTP지원corpus에서PASS입니다. 기준B9CI39178688403은
  5job모두성공해FIND040전체검증을확인했으며확대+회복+이번fieldcontext효과를같이게시해새
  전체CI를받습니다. 버전/의존성/lock/tag/배포·loop1과새소스별전체검증경계는유지합니다.

## 59차 — 파일open/실패/export후정상편집회복

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-editor-recovery-6n1ph96d`와
  [spec/PNG/history·오류·다운로드timeline](review_evidence/editor_recovery_verification.json)을 보존합니다.
- 실제filepicker로유효A를열어편집후malformedJSON/validJSON의missingcolumnspec을열면
  기존spec/PNG/history/layout과화면그림은그대로이며오류/draft는보존됩니다. 유효B는fresh
  history로열리고오류가사라졌습니다. 소스파일A/bad/B의원bytes는마지막까지불변입니다.
- 실제renderer._save_figure의SVG저장만합성OSError로실패시켜GET/fig.svg의HTTP400/
  text/html(부분SVG아님)을확인했습니다. 실제render/finallyclose를거쳐기존state/PNG/history/
  layout/Figure수가보존됐고PNG편집은계속됐습니다. Fault를해제하면SVG200/image/svg+xml의
  최신title과다운로드specJSON=현재state가맞습니다. 미지원JSONexport/PGFbundle을가정하지않습니다.
- 새실제browser1·관련229통과/Windows환경6skip(5symlink권한/1POSIXmode)·실제browser4통과/
  29deselected(no skip)·floor43통과/4symlinkskip/3059deselected/경고13·양platformtype/
  Ruff249/계약/packaging9명령exit0·변경testactiveLSPclean입니다. 13은모두3종Pyparsing입니다.
- 최초연결browser실행의Openfiguretimeout은file-read후접힌Opensection을재확인하는기존
  househelper방식으로보완했습니다. 초기실패log/receipt와최종9명령재실행을구분했고제품
  commit/drop규칙이나새기능을바꿨다고하지않습니다. UI오류는제출파일path/traceback을
  불필요하게넣지않았지만EDIT-07의CLI/agent정보정책전체검토까지완료했다고하지않습니다.
- EDIT-06은현재지원파일/PDF·SVGexport/PNGpreview/JSONdownloadcorpus에서PASS입니다.
  Runtime/FIND/의존성/버전/lock/tag/배포변경없이newB9CI39178688403을보호해확대검증과
  함께로컬보존하며응답순서효과의새전체CI·loop1은별도유지합니다.

## 58차 — DPR/확대preview의drag·키보드·undo/redo

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-scaled-preview-1p1d6dg4`와
  [3scale별실제pointer/data/frame](review_evidence/scaled_preview_verification.json)을 보존합니다.
- 실제Chromiumcontext의[DPR1/CSS1/page1],[DPR2/CSS1.25/page1],[DPR2/CSS1/page1.25]를
  검사했습니다. CSSzoom과CDPEmulation.setPageScaleFactor의visualViewport확대를정확히
  구분하고window.devicePixelRatio/visualViewport.scale도실제값을assert했습니다. 물리모니터/
  모든OS/browser-nativezoom을검증했다는뜻은아닙니다.
- Spec6×3inch/600DPI/selectedpanel1의previewnatural크기는모두2000×1000입니다. Inverted
  logx/y2log의mouseaxes.4/.65는기대10^1.2/10^2.3과2.5%CSSpointer오차로맞고ArrowRight의
  imagefraction+.02는datax를줄입니다. 실제HTMLfraction에서역변환한keyboard값도3e-5
  상대오차로맞고HTMX후handlefocus/undo정확한drag값/redo정확한key값이유지됐습니다.
- DPI600/size/primarytext/빈다른panel은불변이고specJSON도같습니다. 새optionalbrowser3case,
  관련178통과·실제browser선택8통과/28deselected(no skip)·floorpure7통과/3099deselected/
  경고289·양platformtype/Ruff248/계약/packaging9명령exit0·변경testactiveLSPclean입니다.
  289는전부10종Pyparsing이고browserfile을최소의존성roster에넣지않았습니다.
- EDIT-02는이emulatedChromium/현재data-editcorpus에서PASS이며LAY-09의75DPIdense
  geometry와물리hardware일반보장은별도로남깁니다. 제품runtime/좌표정책/FIND추가는없습니다.
- 기준4bcCI39175434805는5job모두성공해대기D535응답효과+B9공유test를이번iteration시작에
  먼저게시했습니다. Origin/HEAD당시B9일치/newCI39178688403진행을확인했으며새효과전체검증은
  아직입니다. 현재확대test/doc은로컬보존하고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 57차 — 두tab/rawaction의공유session직렬화

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-shared-session-jmjawfeq`와
  [도착/commit/spec·PNGtimeline](review_evidence/shared_session_verification.json)을 보존합니다.
- 실제browser두page와rawJSONactionformclient를같은session에연결했습니다. 첫후보render를
  lock안에서보류한동안B/rawbody도착은관찰됐지만commit0/state·PNG초기는그대로입니다.
  Release뒤허용순서[A,B,raw]/[A,raw,B]중하나로만3commit하고서로다른title/suptitle/size
  field가모두남아순수apply와같습니다. FIFO공정성은가정하지않습니다.
- 최종cachePNG는최종spec을다른EditorSession에서렌더한bytes와같고두tab은새로고침후
  최신title/size를읽었습니다. Activepanel0을공유하는범위이며tab별독립selection/livebroadcast/
  원격협업/충돌거절revision을추가하지않았습니다. 같은field의commit순서정책은그대로입니다.
- Rawclient는실제/action/rawform의JSONSetSize를보내HTTP200text/html/UIgeneration을
  받았습니다. 이를JSONRPC라고가정하지않고EDIT-09machinecontract검토와구분했습니다.
- 새실제browser1·관련169통과/non-WindowsAPIguard1skip·실제browser선택4통과/31deselected
  (새case포함/no skip)·floor8통과/3098deselected/경고13·양platformtype/Ruff247/생성계약/
  packaging9명령exit0·변경testactiveLSPclean입니다. 13은모두3종Pyparsing입니다.
  기존privatefixtures/render/read/commitspy는실제함수를호출하며PNG/state를가짜로대체하지않았습니다.
- EDIT-05는현재로컬공유sessioncorpus에서PASS입니다. 추측한mp.to_dict는기존Spec.to_dict로
  고친테스트출력코드문제이며제품API를바꾸지않았습니다. Runtime변경/FIND추가없고4bcCI
  양Rust/min성공·양Python진행을보호해대기응답순서효과와함께로컬보존합니다. 버전/의존성/
  lock/tag/배포·loop1과새효과의별도전체CI경계는유지합니다.

## 56차 — 늦은HTMLfragment의최신view덮어쓰기복구

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-response-order-gz8ecguk`와
  [실제before/after요청·DOM·pixeltimeline](review_evidence/response_order_verification.json)을 보존합니다.
- **FIND-040:** servercommit이직렬이어도첫HTML응답을브라우저route에서보류하고둘째를
  먼저전달한뒤첫째를풀면DOMtitle은older-first로되돌아가고spec/PNG는newer-second였습니다.
  실제old-respond-helperprivate대조가의도한exit1로실패함을따로기록했고통과수에넣지않았습니다.
- 기존sessionlock내부의reply순서를내부_view_generation으로세고HTMXHTML에추가header를
  보냅니다. beforeSwap은이미표시한generation보다오래된view만버려scroll/focussnapshot도
  덮어쓰지않습니다. 요청/두action은모두history에남고새queue/도메인revision/specfield/
  인증토큰/epoch/persistence를만들지않았습니다. Header없는기존처리는보존합니다.
- 실제Chromium에서generation1을나중에풀어도2의DOM/spec/decodedPNGpixelSHA가일치합니다.
  PageJS/failedrequest오류0·action둘다200이며console의정확한/favicon.ico404는별도기록해
  다른오류까지무시하지않습니다. Body중첩없음/기존legenddrag/titlekeyboard/nudgeburst/
  panel교체/scroll·focus회귀도통과했습니다. Counter는undo/redo/reset/open/실패import/
  panel선택뒤증가하고readonlycontenttype/SpecJSON은그대로입니다.
- 새browser1/pureHTTP2·관련179통과·실제browser8통과/26deselected(no skip)·floor2통과/
  3104deselected/경고13·양platformtype/Ruff246/계약/packaging9명령exit0·변경5경로activeLSP
  clean입니다. 13경고는전부3종Pyparsing입니다. 테스트의JS문자열길이/partialedit는바로잡았고
  rawpost응답을JSON이라고가정하거나내부viewcounter를권한으로사용하지않습니다.
- EDIT-03/04는현재로컬HTMXfragment/previewcorpus에서PASS입니다. EDIT-02zoom/highDPI,
  EDIT-05두탭/agent정책은별도로남깁니다. Server재시작시page새로고침의로컬세션한계를
  명시하며기준4bcCI39175434805양Rust성공/3Python진행을보호해효과unit은로컬보존합니다.
  이전CI를새응답순서수정에소급하지않고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 55차 — y2datahandle의실제좌표frame복구

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-coordinate-frames-blyo8vp1`와
  [15frame대조·실제browser·roundtrip](review_evidence/coordinate_frame_verification.json)을 보존합니다.
- **FIND-039:** Pythoneditor의모든text/annotate가primaryylim/scale을받아유효y2log100이
  primary축상단에clamp됐고실제drag의기대y199.526대신2.605139를저장했습니다. 초기5회귀가
  수정전실패했고renderedprimaryAxes→secondaryAxes참조로실제y2context를추출해해당entry만
  전달했습니다. View는per-entryy범위/scale을사용하고기존primarymetadata/fallback은보존합니다.
- Dataanchor는자기축,명시title은axesfraction,legend는figurefraction으로구분합니다.
  96/150/300DPI·4×3/5×4/6×3inch·1/2panel의15before/afterhandle표에서y2만맞게이동하고
  primary/title/legend는그대로입니다. Renderer의실제transData/transAxes/transFigure와
  JSONroundtrip도맞습니다. 동일anchorhandle겹침이라는초기QA를분리한뒤실제잘못된값을재현했습니다.
- 실제Chromium/Chrome mouse+HTMX에서selectedpanel1·invertedlogx/logy2target.4/.65는
  x10^1.2/y10^2.3와2%pointer허용오차로맞고primary/다른panel불변·undo/redo가통과했습니다.
  비지원polartext는원래validation거절로기존state/PNG/layout을유지하므로새극좌표transform/
  control숨김/annotation좌표옵션을만들지않았습니다.
- 새pure5와browser1은분리해최소환경에Playwright를추가하지않았습니다. 관련209통과/
  non-WindowsAPIguard1skip·실제browser선택6통과/27deselected(새test포함/no skip)·floor17통과/
  3087deselected/경고289·양platformtype/Ruff244/계약/packaging10명령exit0·변경6경로activeLSP
  clean입니다. 289는모두10종Pyparsing입니다. 가정한JSONexport를추가하지않고기존to_json/
  from_json을사용했으며typedguard를두어Any/cast/ignore는없습니다.
- PLOT-11은현재PythonCartesian지원corpus에서PASS로PLOT01..12의명시검토를마쳤지만모든
  API/nativeparity/previewgeometry보장은아닙니다. 기준b8CI39171315500은5job모두성공해
  대기alpha+좌표runtime을함께게시하고새전체CI를받습니다. 버전/의존성/lock/tag/배포·loop1은유지합니다.

## 54차 — annotationalpha누락복구와overlay정렬

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-overlay-alpha-dm2wvg0w`와
  [artist/수작업·before/after](review_evidence/overlay_alpha_verification.json)/
  [제한비교그림](review_evidence/annotation_alpha.png)을 보존합니다.
- **FIND-038:** annotate의유효alpha가Text/arrowprops에전달되지않아alpha0도불투명했습니다.
  새초기11회귀가수정전전부실패했고공통_draw_marker_layer의해당branch에서nondefaultalpha를
  text/arrow모두에전달했습니다. 기본1은기존RGBAcolouropacity를유지해호환성을보존합니다.
  기존RGBAopacity12번째회귀도추가했으며별도API/schemafield/기본zorder변경은없습니다.
- Primary/y2·arrow유무·alpha0/.35·기본opaque/RGBA·SVG양쪽opacity와alpha0전체canvas
  대조가통과했습니다. 이전helper를privateAST로대조한golden의변경channel9967→0이며
  after는무annotationreference와pixel동일합니다. 비교PNG는resize된합성입력그림이지
  모든font/backend/인쇄환경golden이아닙니다.
- 음수/0bar·불균형/중복범주의dodge중심/실제값/절대CI가원행과맞습니다. Signedstackplot
  수작업경계0→[1,2,3]→[5,1,5]→[3,4,6],중복/unsortedband경계edge순서와x/yerror방향도
  확인했습니다. Nativeartistzorder/clip표는그대로이며layer호출순서가모든종류의zorder를
  강제한다거나새clip옵션을지원한다고하지않습니다. 초기annotationclipFalse라는QA가정은
  실제True로바로잡았지기존clip동작을바꾸지않았습니다.
- 새12/관련245통과·실제floor12통과/3087deselected/경고13·양platformtype/Ruff242/
  계약/packaging9명령exit0·변경3경로activeLSP clean입니다. 13경고는모두3종Pyparsing이며
  최초canvasBase타입stub은Agginstance검사로고쳐Any/cast/ignore를넣지않았습니다.
- PLOT-09/12는현재지원overlaycorpus에서PASS입니다. PLOT-11browser좌표/drag는별도로남깁니다.
  기준b8CI39171315500은양Rust/최소환경성공·3.10/3.12Pytest진행중이라새효과unit은로컬
  보존합니다. 이전CI를새alpha수정에소급하지않고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 53차 — sharedaxes/독립축과log유효영역

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-axis-contracts-jrvsnxzu`와
  [9축표·3충돌·8log결과·backendpixel](review_evidence/axis_domain_verification.json)을 보존합니다.
- Col공유의0/2와1/3은limits/ticks가같고empty도같은group입니다. 마지막명시bounds의
  역방향200..2는해당col만갱신하며독립y범위/labels/y2log1..10000을덮어쓰지않습니다.
  Named0/3만연결하고다른축은별개이며scale/limits충돌·mode혼합3경계는거절합니다.
  범주충돌/2D·3D·polar부분집합/griddensity분리는기존회귀도재실행했습니다.
- Legacyline/scatter의비양수x는원자료에남고nativeLogTransform으로화면밖clip됩니다.
  Typed파생interval비양수는그리기전에명시실패합니다. 양수1e-200..1e200측정log축과
  legacylinearcolour-1..1은독립입니다. Typedheatmap의실제LogNorm은명시mask의-1/0을
  제외해원값을유지하며양수norm0/.5/1이맞고cell축은linear입니다. 비양수unmasked/vmin·
  미지원symlog는거절합니다. 초기logcolour미지원이라는QA가정은실제지원계약으로고쳤습니다.
- 관련축선택214통과/458deselected·실제floor214통과/2873deselected/경고1843·
  양platformtype/Ruff241/계약/packaging기본9명령exit0입니다. 1841은Pyparsingdeprecation,
  2개는별도8casefloor대조로Matplotlib3.8image.py463/468상수linear1e308guard임을특정했습니다.
- 별도floorpixelprobe는큰상수원값을보존하며2셀RGB가norm기대값과1code이내로일치했습니다.
  반복draw라경고4개가났지만잘못된pixel4개가아닙니다. Werror저장실패는이전PNG/Figure/tmp를
  보존/정리합니다. Nativeguard의dv×1e7intermediateoverflow는데이터손상으로세거나숨기지않고
  명시backend한계로기록했습니다. 추가2대조까지총11명령exit0이며Runtime변경/FIND추가는없습니다.
- PLOT-05/10은현재지원corpus에서PASS이며범용극단축/모든viewer보장은아닙니다.
  기준3bCI39166807390은5job모두성공해FIND-037의실제runtime전체검증을확인했습니다.
  대기분포/pairing/축문서를함께게시하고새문서sourceCI를받되버전/의존성/lock/tag/배포·loop1은유지합니다.

## 52차 — 통계전처리의관측index/원래쌍보존

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-observation-pairs-4tmw6l_y`와
  [12경로/원래row·정확mean·거절](review_evidence/observation_pairs_verification.json)을 보존합니다.
- 고정10행의x/y/group/weight/unit/style/size결측위치를다르게뒀습니다. ECDF/hist/KDE1D는
  row0/1/6/7/8/9,xyKDE2D/lineplot은0/6/7/8/9,weightedcat집계/violin은0/2/6/7/8/9,
  unweightedbox는0/2/4/5/6/7/8/9,unweightedcount는3만제외했습니다. 필수role이다르므로
  같은index로억지통일하지않고사용하지않는y/x/weight결측은그대로두었습니다.
- Semanticlineplot의추가style/size와stat행교집합은0/7/9,unit필수clusterbar는0/2/6/8/9로
  맞습니다. 원래values/weights/units를함께추적해FractionweightedmeanA103/7또는unit67/5,
  B33/2와n/n_units가맞고histA질량3/3·B0/2도원행weight에서나옵니다.
- Regplot선택결측은조용히drop하지않고명시거절하며B만선택하면row4/5/6/8의실제scatter쌍을
  그대로그립니다(미사용weights결측/0은관계없음). 필수nonnumericx/음수·bool·문자weight4경계는
  validation/render가거절하고caller상태를보존합니다. 명시제외hue의해당값은검증대상에섞지않습니다.
- 기존관련경계선택388통과/444deselected·실제floor388통과/2699deselected/경고489·
  양platformtype/Ruff241/생성계약/packaging9명령exit0입니다. 489는같은floor실행에서모두
  10종PyparsingDeprecationWarning으로분류했습니다. 전체suite통과수로바꾸어쓰지않습니다.
- STAT-08은현재지원전처리/선택corpus에서PASS이며STAT01..08은각명시범위의검토를마쳤지만
  보편통계·adapter·UI인증은아닙니다. 계산/validator/새test/framework는없고3bCI39166807390
  양Rust성공/3Python진행을보호해전차분포와함께로컬보존합니다. 새회귀수치전체CI·버전/
  의존성/lock/tag/배포·loop1의별도경계는유지합니다.

## 51차 — box/violin수작업기준과jitter재현성

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-distribution-jitter-320_pdy8`와
  [8box/24profile·위치·hash/RNG](review_evidence/distribution_jitter_verification.json)을 보존합니다.
- Odd[0,1,2,3,100]Q1/median/Q3=1/2/3·1.5IQRwhisker0/3·outlier100,even[0,1,2,3]
  =.75/1.5/2.25·whisker0/3,단일7/상수4를수작업값과대조했습니다. 양orientation의실제
  patchquartile/median/whisker/flier가맞고pairedmissing3행을제외한사용row0..12를보존하며
  empty범주에가짜box를만들지않았습니다.
- 서로다른5/4/10/12표본4cell의Fraction불편표본분산/Scott/NormalDistPDF·선형분위수와
  area/width/count×common/local의24profile을대조해최대오차5.55e-16입니다. Area는
  명시peak-reference정의이지유한cut/clippolygon면적을항상1로강제한것이아닙니다. Weighted
  stepquantile/질량정의·inner/geometry는기존weightedviolin회귀로분리하며box지원으로확대하지않습니다.
- 기존stripplotdefault_rng0±jitter(.15default/명시0)을독립16위치와대조했습니다. 다른random
  layer의전후추가에도같은series위치가같고NumPy/Python전역RNG는변하지않았습니다.
  PYTHONHASHSEED1/777두프로세스·반복PNG/PDF/SVGhash도같습니다. 서로다른spec의색상/
  zorder까지같은이미지나통계적으로독립layerstream이라고주장하지않으며새seed옵션도없습니다.
- 관련408통과·실제floor407통과/2680deselected/경고1649·양platformtype/Ruff241/생성계약/
  packaging9명령exit0입니다. 1649는전부10종PyparsingDeprecationWarning으로같은floor
  실행에서분류했습니다. 큰Windowsheredoc잘림SyntaxError는실행전실패라test결과로세지않고
  privatefile로분리했으며LayerSpec실제import경로도바로잡았지제품API를바꾸지않았습니다.
- STAT-06/07은현재지원corpus에서PASS입니다. Productruntime/새test/framework는없으며
  진행중3bCI39166807390의양Rust성공/3Python진행을보호해문서unit은로컬보존합니다.
  이전회귀수치효과의새전체CI가아직필요하며버전/의존성/lock/tag/배포·loop1은유지합니다.

## 50차 — KDEbandwidth/적분/퇴화입력의독립대조

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-kde-review-7k93qkbn`와
  [분수moment·24mixture·grid/적분·두mode](review_evidence/kde_integral_verification.json)을 보존합니다.
- Weightedx[-1,2,4]/w[1,2,3]의정확한분수mean5/2·unbiasedvariance117/22·neff18/7을
  Scott/Silverman/명시factor.5×adjust1.25와대조했습니다. Common/개별·PDF/CDF·clip유무의
  24설정/각2049grid를독립NormalDistmixture로비교해최대절대오차2.22e-16입니다.
- 유한support의analyticCDF차와직접trapezoid오차최대8.94e-9를구분했습니다. Clip은
  fitrow/bandwidth/꼬리질량을재정규화하지않고CDF시작도0으로rebasing하지않습니다.
  Singulargroup질량4/총10은공통분모에남아유효group면적.6이며가짜Gaussian/grid를
  만들지않습니다. Emptygroup은별도0표본으로구분했습니다.
- Bimodal[-3.1,-3,-2.9,2.9,3,3.1]은분산1351/125·factor.04·4095grid에서두peak
  -2.999878/+2.999878을확인했습니다. 기존285case의empty/constant/singular·극단bandwidth/
  단위·1D/2D/grid·log·CDF·비지원weightedgrid·row순서/청크·export/RNG도재실행했습니다.
- 관련359통과·실제floor285통과/2802deselected/경고317·별도warningcollector재실행도
  285/317동일·양platformtype/Ruff241/생성계약/packaging9명령exit0입니다. 317은전부10종
  PyparsingDeprecationWarning이며새수치runtime경고는없습니다. 최초order옵션probe는
  지원거절을확인후기존hue_order로고친QA이지제품결함/실행test통과가아닙니다.
- STAT-05는현재Gaussian/지원조합corpus에서PASS입니다. Typedskip와legacyconstantfallback,
  상대weights정의는유지하며새커널/모델/normalizer/testfarm은없습니다. 기준efCI39162647649는
  5job모두성공해대기수치수정+histogram+KDE를함께게시하고새효과CI를받습니다.
  버전/의존성/lock/tag/배포·loop1은유지하며기준성공을새회귀수정전체검증으로소급하지않습니다.

## 49차 — histogram경계/weights/density독립질량대조

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-histogram-review-t8dyma2q`와
  [Decimal38행·기존회귀·경고분류](review_evidence/histogram_normalization_verification.json)을 보존합니다.
- 중복test를추가하지않고기존histogram186case의경계값/비균일bins/선택hue/원시log폭/
  stack·dodge·bars·step/빈곡선/큰weights/단조CDF/legacyNumPy대조/codec/editor/3format·RNG를
  현재코드로재실행했습니다. 새로운normalizer/API/default는없습니다.
- 별도80자리Decimal은edges0/1/3/6·weights·좌우경계/마지막포함·범위밖행·결측을직접합산해
  지원19설정×2group=38행을대조했습니다. In-range질량15(A9/B6)만분모이고outside198은
  제외합니다. CountA1/3/5·B0/2/4에서common-density적분.6/.4·개별적분1/1이며높이합이
  아닙니다. 누적은질량prefix/정규화확률이며미지원cumulativefrequency를helper에직접넣어
  결함으로세지않습니다. Dodge그림면적과원래bin폭의통계정규화도구분했습니다.
- 관련269통과·실제floor186통과/2901deselected/경고257·별도warningcollector재실행도186/
  257동일·양platformtype/Ruff241/생성계약/packaging9명령exit0입니다. 257은모두10종
  PyparsingDeprecationWarning이며제품수치RuntimeWarning이아닙니다. 초기없는histplot.py
  filename명령은pytestexit4/no testsran으로보존하고실제test_layers로수정해통과와구분했습니다.
- STAT-04는현재지원weighted/legacycorpus에서PASS입니다. Constantpositive로그autoedge
  명시실패·rawmassoverflow·빈범주/금지조합의기존규칙을유지합니다. 원격기준efCI는4성공/
  3.10Pytest진행중이라대기수치수정과문서unit을로컬보존합니다. 버전/의존성/lock/tag/배포·loop1은유지합니다.

## 48차 — 퇴화회귀와covariance단위손실복구

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-regression-degenerate-hpq0st5v`와
  [before/after·조건수·독립OLS공식](review_evidence/regression_degenerate_verification.json)을 보존합니다.
- **FIND-037:** legacyhelper의rawresponsecovariance는1e-250에서underflow해정규화band최대폭
  3.13594가0이되고1e250에서는nonfiniteband가소실된채성공했습니다. Clustereddegree10은
  정규화design조건수1.784e18/rank3(11parameter)인데경고후예측최대4.67e10을반환했습니다
  (관측최대121). 수정전새19회귀가4실패/15통과임을확인했습니다.
- 공통_regression_fit에서predictormagnitude/unitrange와response를covariance전에정규화하고
  원단위로복원합니다. Scoped산술/warning을원인있는ValueError로전환하고nonfiniteband를
  거절해raw경고와가짜band를반환하지않습니다. Legacy/typed공통호출자만고쳤고새fallback/
  조건수임계값/API/schemafield는없습니다. 기존mean-fitnormalapproximation정의는유지합니다.
- x0..4/y[1,2,1,4,3]의독립기울기.6/절편1/RSS3.2/MSE3.2÷3와z(.975)공식을써서response
  1/1e-250/1e250·legacy/typed의200grid곡선과bandpolygon끝을원단위로대조했습니다.
  predictor1e-250/1e250/1e308helper계산·부족/상수/높은degree/결측·rank실패의기존파일/
  Figure/tmp/spec복구도확인했습니다. 유한helper계산은모든거대Matplotlib축layout보장이아닙니다.
- 새19/관련201통과·실제floor19통과/3068deselected/경고13·양platformtype/Ruff241/
  계약/packaging8명령exit0·변경효과2경로LSP clean입니다. Optionalrobust/logistic/LOWESS기존
  독립reference·완전분리·RNG/출력회귀도포함합니다. STAT-03은이경계corpus에서PASS입니다.
- 기준efCI39162647649는양Rust성공/3Python진행중이라새효과unit은로컬보존합니다.
  버전/의존성/lock/tag/배포·loop1은유지하며기준성공을후속수치수정에소급하지않습니다.

## 47차 — projection좌표와연속색상guide의실제의미

- 로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-projection-colours-ciamlju_`와
  [독립좌표/색상기대값·회귀](review_evidence/projection_colour_verification.json)을 보존합니다.
- Quiver명시scale1/width.005와비대칭6×3inch·x0..4/y0..2에서세axis/diagonal벡터의
  실제polygon끝을independenttransData(x+u,y+v)와1e-5displaypixel이내로대조했습니다.
  3Dline/scatter의비단조x[1,7,3]/y[11,5,2]/z[19,23,13]와polar0/π2/π의동/북/서가
  원자료를유지합니다. 비정방matrix/mesh는기존numericgeometry/newlayers도현재재실행했습니다.
  미지원polarhist는fallback없이ValueError입니다.
- 독립2panelheatmap의explicitvmin/vmax0..10/-10..20·mask·RGBA포화끝·각colorbarmappable/
  label/domain을검사했습니다. TypedmatrixNone은기존finite계약상거절되고mask용유효999는
  그리지않습니다. Legacyc의constant/allmissing/mixedmissing은mask와유한guide를유지합니다.
- Numerichue_norm은-5/20범위밖행도보존하고끝색을포화시키며guide0/5/10을만듭니다.
  이guide는colorbar가아닌명시numericlegend입니다. 초기typednull/semanticcolorbar라는QA
  가정은유효mask·명시null거절·실제legend계약으로고쳤으며제품오류로세지않습니다.
- 새12/관련229통과·실제floor12통과/3056deselected/경고13·양platformtype/Ruff240/
  계약/packaging8명령exit0·변경2경로LSP clean입니다. PLOT-07/08은현재지원조합corpus에서
  PASS이지모든projectionviewer나미지원scaleoption인증은아닙니다. Legacyc자동norm과
  typedheatmap/semantics의명시범위를구분하며새API/schemafield는추가하지않았습니다.
- 기준b777CI39159051900의4job은성공·3.10은sitebuild진행중이라대기준비감사와함께
  로컬보존합니다. Productruntime/버전/의존성/lock/tag/배포·loop1은유지합니다.

## 46차 — fixture/evidence분리와계약결정기록

- [준비감사표](REVIEW_PREPARATION.md)와 [inventory/검사](review_evidence/preparation_audit_verification.json),
  로컬 `C:\Users\mud\AppData\Local\Temp\mudplot-preparation-audit-hmenwe0p`를보존합니다.
- 고정reviewfixture5개를실제consumer/생성방식/codec-only·renderable범위로분리했습니다.
  SourceJSON과공유evidenceJSON42개의snapshotSHA/size/parse결과를보존했고profile절대경로/
  대표privatekey/token패턴은0hit입니다. 이는모든임의텍스트의비밀부재인증이아니며입력scope도
  읽어합성자료임을확인했습니다. LocalTemp원본로그/전체환경은공유물로복제하지않습니다.
- Randomhistoryseed20261016/24301·고정fixture의noRNG를기록하고synthetic입력과결과receipt/
  rawloghash를구분했습니다. 새판별기API/자동redaction으로원본이라고속이는정책은없습니다.
- Mutable상태/snapshot·세batch경계·openFigure·명시crop·journal우선순위·최종HEXreport·
  유한pattern·trustedPGF/sidecar·source-tools/wheel·Rustcontrolsubset·release권한의충돌표에
  기존/수정주장과근거/선택이유를기록했습니다. 새runtime호환성변경승인을추론하지않습니다.
- 기존관련313통과/명시smallgroupMPL경고2·양platformtype/Ruff239/생성계약/packaging7명령
  exit0입니다. Prep문서의19개명시artifact/consumerlink도실제존재를검사했습니다. 초기잘못된
  consumerfilename가정은실제fixtureloadgrep로고쳤고새coverage로세지않았습니다.
- BASE-06/07은현재최소재현물/결정기록범위에서PASS이며BASE-05의150ID별symbol/test매핑은
  여전히진행중입니다. Productruntime/artifact를바꾸지않고b777CI39159051900을취소하지않도록
  문서unit은로컬보존하며버전/의존성/lock/tag/배포·loop1은유지합니다.

## 45차 — 생성표현의의도적drift회귀

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-generated-drift-hejhydoe`와
  [drift/registry/복구 요약](review_evidence/generated_drift_verification.json)을 보존합니다.
- 먼저기존check_schema_sync.py를실행했습니다. 세생성artifact만소유tmp사본에복사해
  baselineexit0→의도json/textdriftexit1+artifact별재생성명령→원bytes복구exit0을검사했습니다.
  Realrepoartifact를깨거나generated를수동패치해통과시키지않았습니다.
- Action36개/field목록·layer37개·LayerSpec공식field·capabilities·generatedreference가
  일치합니다. LayerSpec.type은기존구조적string/default등록kind이며kindsemantic검증은
  별도입니다. Enum이라고가정한최초QA를실제계약에맞췄고schema강화는하지않았습니다.
- 새4case·관련231통과·실제floor4통과/3052deselected/경고13·양platformtype/Ruff239/
  packaging8명령exit0·변경2경로LSP clean입니다. JSON-11은이생성/등록corpus에서PASS이며
  JSON-09의모든nullable의미나BASE05/06/07감사까지완료했다고하지않습니다.
- Productruntime/생성파일의내용은바꾸지않고test/floor추가만로컬보존합니다. 진행중
  161CI39155483298을취소하지않으며버전/의존성/lock/tag/배포·loop1은유지합니다.

## 44차 — 출력권한/잠금과callerFigure소유권

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-output-lifecycle-1cdspizk`와
  [Windows실패/80Figure/자원시계열](review_evidence/output_lifecycle_verification.json)을 보존합니다.
- JSON/PNG/PDF/SVG의읽기전용target·실제WindowsCreateFileWdeny-delete잠금8case는
  PermissionError로끝나기존bytes/다른파일을보존하고소유Figure/tmp를회수했습니다.
  Missingparent/directorytarget/write/flush/sync/replace의기존faultfixture도현재코드로재실행했습니다.
- 실제디스크소진대신ENOSPC4case를주입해errno/원문bytes/정리를검사했고잘못된확장자도
  target을건드리지않았습니다. 초기JSONdumpmock은실제Pathwrite경로가아니라실패를주입하지
  못한QA였으며owned.tmpopen의ENOSPC로고쳤습니다. 제품결함이나실제diskfull로세지않습니다.
- 성공render/saveFigure가열린채반환되고callerclose/GC뒤weakref가해제되는17회귀를추가했습니다.
  별도20cycle×render/png/pdf/svg=80Figure관찰은open/liveFigure/tmp0·handle215→216·
  warmRSS85,491,712→final90,804,224bytes·peak245,747,712입니다. 선형Figure보관은없었지만
  cache/allocator/nativeworking-set과1handle차이를모든장시간누수부재로확대하지않습니다.
- 관련128통과/WindowsOSskip6/명시impossibleMPL경고8·실제floor17통과/3035deselected/
  경고13·양platformtype/Ruff238/계약/packaging8명령exit0·변경2경로LSP clean입니다.
  새Windows실제권한case는타OS에서명시skip하며root권한/ACL전체를인증하지않습니다.
- OUT-04/05는이controlledfailure/ownedFigurecorpus에서PASS이며PERF-04의장시간문제는
  그대로진행중입니다. Productruntime을바꾸지않고현재161CI39155483298을취소하지않도록
  test/doc은로컬보존하며버전/의존성/lock/tag/배포·loop1은유지합니다.

## 43차 — 유한pattern·1-column컬러/흑백·대외문구

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-print-review-iiok6ccg`와
  [78group/pattern표·물리설정·검토](review_evidence/encoding_print_verification.json),
  [컬러/흑백contact](review_evidence/one_column_encoding.png)을 보존합니다.
- 기본hatch6종을7group의bar/box/violin·marker8/style4를9group의line/scatter에서2panel
  artist/legend와대조해일치·반복을확인했습니다. Pairedmarker/style도LCM8이지32개독립
  보장이아닙니다. Box(value,group)의범주axis모드에legend를가정한초기QA는명시cat/value/hue
  fixture로고쳤고제품오류로세지않았습니다.
- LCH등명도·linearY흑백proxy·범주구분을분리했습니다. IndependentIECdecode/Yweights/
  encode와grayscale_srgb가맞고equalLCH팔레트는흑백metric을통과하지않습니다. 모든printer/
  achromatopsiaviewer예측이라는docstring도측정proxy로한정했습니다.
- IEEE1column(252/72.27inch),300DPI,font8/8/9/7pt의line0.6pt/marker2pt·좁은bar·alpha.18band
  컬러/흑백4쌍을검토했습니다. 선/점/pattern은보완하지만작은marker/dash비교에는검토가
  필요하고6band는흑백에서구분이약했습니다. 범주축소·경계선/직접label·분리panel을권장하며
  swatch점수를그대로가독성판정으로삼지않습니다. Contact는비교용resize이고원물리plate는보존합니다.
- README/한국어/생성REFERENCE/색상docstring/디자인gallery의무제한색상수보장을좁혔습니다.
  Gallery는paper5preset·정상+3CVD+흑백proxyrow로설명하며모든row인증을주장하지않습니다.
  Palette최적화/패턴주기/임계값은바꾸지않았고코드변경은sample선택/문구·회귀입니다.
- 관련77통과·site9통과·실제floor8통과/3027deselected/경고13·Ruff237/양platformtype/
  계약/packaging9명령exit0·변경7경로LSP clean입니다. COLOR-06/07/09/10은이측정·검토/
  문구corpus에서PASS이지정식printer/관찰자접근성연구가아닙니다.
- 기준16aCI39148609011은5job전부성공해대기bb75723report수정과함께게시하고새CI를받습니다.
  버전/의존성/lock/tag/배포·loop1은유지합니다.

## 42차 — 최종RGB팔레트지표와평가조건

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-palette-report-u5wf2on9`와
  [최종RGB/pair/조건/범주경계](review_evidence/palette_report_verification.json)를 보존합니다.
- **FIND-036:** report는nominalLCH명도차3으로paper7/vivid7을grayscale_safe로표시했지만
  실제HEX출력은각2.7920868975(pair1,2)/2.7972618066(pair0,1)였습니다. 새18회귀중13개가
  기존지표/조건누락을드러냈고floatmetric은mappedRGB,report는최종8-bitHEX로고쳤습니다.
- 기존reportkey/signature/기준8·3/생성RGB·LCH·HEX/최적화는유지하고evaluation만추가했습니다.
  ModelMachado2009·정상시각+선택유형·fullseverity1·표현·threshold·measured-only범위를
  명시합니다. Floatcmap/method와HEXmetric이작게다를수있고인쇄/접근성인증이아닙니다.
- [저자Table1](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html)의
  fullseverity3유형matrix와독립IECencode/linearclip기준4입력을대조했습니다. Defaultreport는
  protan/deutan이며tritan/빈CVD선택도정상시각포함조건을명시합니다. 모든severity안전으로확대하지않습니다.
- Paper/vivid의사전N6,softN5에서N-1/N/N+1의출력RGB/최소pair/metric을보존했습니다.
  Paper7/vivid7은이제grayscalefail이며soft6는측정pass할수있어N+1을일괄unsafe로만들지않습니다.
  DegenerateC0동률은candidate0/1/2hue를택하고같은옵션/hue_start의반복·독립processHEXhash와
  globalNumPyRNG보존을확인했습니다. 새randomseed옵션은없습니다.
- 관련141통과·실제floor18통과/3009deselected/경고13·Ruff236/format·양platformtype/
  계약/packaging8명령exit0·변경3경로LSP clean입니다. COLOR-03/04/05/08은이측정범위PASS,
  COLOR-06/07/09/10의흑백패턴/작은그림가독성/대외문구전체는별도미완료입니다.
- 진행중16aCI39148609011을취소하지않고unit은로컬보존합니다. 원문/버전/의존성/lock/tag/
  배포·loop1은유지합니다.

## 41차 — style격리와물리DPI간격

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-style-dpi-dgaoc39s`와
  [rc/hash/DPI/preview 요약](review_evidence/style_dpi_verification.json)을 보존합니다.
- Publication/minimal/paper-grid+journal을callerambientrc에서번갈아저장해전체rcParams의
  changedkey0·실패복구를확인했습니다. PNG/PDF/SVG×3variant의반복/독립processSHA가
  동일합니다. 초기freshprocess에callerambientrc를안넣은비교는다른환경이어서QA를맞췄고
  제품styleleak으로세지않습니다. LAY-08은이owned/equivalent환경에서PASS입니다.
- **FIND-035:** 같은dense guide의150/300DPI에서절대pixelpadding때문에물리위치가
  0.02689395inch달랐습니다. Adaptivepad를0.02inch×figDPI로변환해default300DPI의6px는
  유지하고차이는0.01041395inch로줄였습니다. 다른linewidth/data/spec크기는바꾸지않았습니다.
- Editor600DPI10x5inch→2000x1000preview는원래state를유지하고finalpanel과최대
  0.00333334inch차이·1.5pt선폭·SVG720x360pt를유지합니다. Rust는공유CLIpreview경로를
  쓰지만이번단위의새native위치검증은없습니다. 75DPI dense잔차0.14594497inch는남아
  LAY-09는OPEN→RUNNING만반영하며보편저해상도WYSIWYG보장으로세지않습니다.
- 새6case/관련88통과·실제floor6통과/3003deselected/경고13·양platformtype/Ruff235/
  계약/packaging8명령exit0·변경3경로LSP clean입니다. RC복구와geometry를섞어증명하지않고
  oldfullsuite결과는새pad변경의검증으로소급하지않습니다.
- 기준5caCI39142799672는5job모두성공해대기364guide수정과함께게시할수있습니다.
  새sourceCI를받으며버전/의존성/lock/tag/배포·loop1은유지합니다.

## 40차 — 외부legend/다중colorbar/share/y2 복합guide

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-mixed-layout-pjwb8yt3`와
  [before/after bbox·실제출력renderer](review_evidence/mixed_guide_verification.json),
  [visualbaseline](review_evidence/mixed_guides_baseline.png)을 보존합니다.
- **FIND-034:** 동일ungroupedseries의line/scatter범례가반복됐고6x3의2panel+2colorbar+
  sharex/y+secondaryy에서label/외부legend가겹쳤습니다. 초기6회귀가중복으로실패했고그수정
  뒤남은1case가실제y2label겹침을드러냈습니다. 고정1.35axes배율을지우고실측tick/label/
  offsettext와물리ScaledTranslation으로gap을유지해axes축소후재겹침도막았습니다.
- 같은axis/x/y/z/label/citation/href의명시ungroupedpoint/line(2D/3D)만첫guide를공유합니다.
  Rawgroup1/str1·semanticguide·다른열/축/reference/marker는그대로유지합니다. Legend표현
  처리이지원문/기하/style데이터변경이나문자열만으로모든guide를합치는정책은아닙니다.
- 8x3.5/6x3조합의data/축label/legendbbox는침범하지않고PNG/PDF/SVG실제draw_eventrenderer
  에서도labeloverlap0입니다. 최초vector저장뒤Aggcachedrenderer를재사용한QA는측정이
  틀려실제saveevent로교정했습니다. 4.5x2.8secondary조합은한계경고를유지하며canvas를
  늘리거나font를줄이지않습니다. Baseline은dense진단이지보편aesthetic최적값은아닙니다.
- 새14case·관련185통과·실제floor14통과/2989deselected/경고13·양platformglobaltype·
  Ruff234/format·계약·packaging8명령exit0·변경3경로LSP clean입니다. Privatecollector의
  작은nonsecondary에도경고를가정/privatesave에spec누락한실패는control수정이지제품결과가아닙니다.
- LAY-05는이측정corpus에서PASS입니다. 모든artist/폰트/guide배치보장은아니며manualanchor는
  신뢰합니다. 현재5caCI39142799672를취소하지않고renderer단위는로컬보존하며버전/의존성/
  lock/tag/배포·loop1은유지합니다.

## 39차 — systemfont/glyph/fallback과한글 layout

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-font-scope-kguux7cu`와
  [fontfile/glyph/bbox/진단 요약](review_evidence/font_boundary_verification.json)을 보존합니다.
- 없는family는strictfindfont에서거부되고defaulteffect에서는DejaVu로fallbacklog를남깁니다.
  요청spec.family/text는바뀌지않습니다. BundledDejaVuSans의Hangul누락도warning/mathtext
  log로감지했습니다. 현재WindowsMalgunGothic은Hangul은있지만U+2212가없어8722경고를
  냈고NotoSansKR은coverage가있지만normalweight대신100선택log가있었습니다.
- Installed2family의실제fontfilebasename/SHA·glyphindex·titlebbox·메시지를JUnitproperty로
  기록했습니다. 한글/영문/긴그룹의3.4x2.2namedoutsidelegendcase는title/legendbbox가canvas
  안이고spec/size는같았습니다. 이전English/무공백/멀티라인의지원/경고fixture와함께LAY-04와
  LAY-07은이관찰corpus에서PASS입니다. 모든문자/font/OS/가독성인증은아닙니다.
- Missingfamily/glyph는항상독립case로유지하고선택systemCJKfont가없는환경만명시skip합니다.
  Binary배포/자동다운로드/강제minus치환/weight재매핑은추가하지않습니다. Font확인은render
  effect에서하며purecore를import시환경검사로바꾸지않았습니다.
- 관련97통과/예상glyph·impossiblelayout경고14·실제floor5통과/2984deselected/경고26,
  양platformglobaltype·Ruff233/format·계약·packaging8명령exit0·변경2경로LSP clean입니다.
  제품runtime은바꾸지않고경고를suppress하지않았습니다.
- 기준66feCI39139498998은이제5job모두성공했지만대기layoutdiagnostic 변경이전입니다.
  이전로컬단위6ac와함께게시해새CI를받되현재source검증으로소급하지않습니다. 버전/
  의존성/lock/tag/배포·loop1은유지합니다.

## 38차 — automatic text의 불가능 layout 진단

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-layout-probe-izllqm3k`와
  [bbox/경고/CLI/rollback 요약](review_evidence/layout_boundary_verification.json)을 보존합니다.
- **FIND-033:** 공백없는긴자동title/suptitle이잘려도경고없던2case를재현했습니다. Tiny
  multiline은기존Matplotlibwarning이있어별도새오류로세지않습니다. 추가outsidelegend는
  음수workingrect로solver예외가나던기존경로를확인해유효rect만적용하도록고쳤습니다.
- 최종draw뒤자동paneltitle/suptitle·namedoutsidelegend의canvas/상호bbox를1pixel허용으로
  점검해generic UserWarning을냅니다. 입력문자열을log에복제하지않고명시줄바꿈/크기/
  font조정안내를제공합니다. Canvas확대/font축소/원문변경은없고manualtitle/legend는caller소유입니다.
- 지원English/multiline의두panelbbox는작은canvas안에서분리됐고,9before/after extreme
  fixture도초과시진단합니다. CLI는경고stderr+원래PNG크기를유지하며warning-as-error는
  이전출력/원문보존·Figure/staging정리를유지합니다. 새9test·관련145통과/명시impossible
  fixture의MPLwarning8·실제floor9통과/2975deselected/경고21·양platformtype/Ruff232/
  계약/packaging8명령exit0입니다. LSP3경로는2clean/1inconclusive이며type검사를별도보존합니다.
- LAY-06은지원한감지/경고정책에서PASS입니다. LAY-04는CJK/다른font/긴group등이남아
  OPEN→RUNNING만반영합니다. 모든가독성/artist충돌/외부수동위치보장은아닙니다.
- 기준805CI는minimum/양Rust성공·3.10Pyright실패/3.12취소로완료됐고platformhotfix5918/
  preset66fe를이번단위초기에게시했습니다. 새CI39139498998은진행중이며이renderer변경
  이전결과로검증했다고하지않습니다. 단위는로컬보존하고버전/의존성/lock/tag/배포·loop1은유지합니다.

## 37차 — 전체 TeX preset·columns의 실제 출력 크기

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-preset-geometry-mteetbd9`와
  [20조합 file/preview 표](review_evidence/preset_geometry_verification.json)를 보존합니다.
- 실제TEX_PRESETS5개×columns1/2×fraction0.75/1.0의20조합에서vectorpreview·mockimage
  폭·spec·render·PNG/PDF/SVG실제box가일치했습니다. TeX폭은72.27pt/in,vector는72pt/in,
  PNG는100DPI에서1pixel허용오차이며preview는원래PlotSpec을바꾸지않았습니다.
- Journal4개도관례size→tex_size→명시size의마지막sizeaction을확인했습니다. Activejournal
  rcfont/linewidth는theme위에적용되는기존우선순위를유지합니다. `.journal(None)`은size를
  유지하고명시themefontfield를드러냅니다. `.tex_size`가label_size도설정하므로body size만
  바꾸면명시label_size가남는것은별개입니다. 초기QA의잘못된15ptlabel가정은고쳤습니다.
- 기존API설명은font도후속setter로무조건이긴다고과장해실제registry우선순위와맞게
  문서만고쳤습니다. 새fontoverrideflag/렌더순서변경으로기존publication교정을바꾸지 않았습니다.
  Preset수치출처는repoTeXregistry/comments이며최신공식publisher가이드전체인증이 아닙니다.
- 관련58통과·실제floor24통과/2951deselected/경고13·Ruff231/format·양platformglobalPyright/
  계약·packaging8명령exit0·변경3경로LSP clean입니다. JUnitproperty20행에서실제box를읽고
  보존했습니다. Runtime AST는docstring을제외하면그대로이며LAY-03은이registry범위에서PASS입니다.
- CI805의platform실패hotfix는로컬에이미보존됐고남은floor job을임의취소하지않았습니다.
  이번test/doc단위도로컬보존후baseline완료시함께게시합니다. 버전/의존성/lock/tag/배포·loop1은유지합니다.

## 36차 — Linux Pyright의 Windows API factory 경계 복구

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-ci805-failure-y9h_wgda`와
  [실패step/양platform 검사 요약](review_evidence/platform_guard_verification.json)을 보존합니다.
- **FIND-032 (검증 도구/type):** 기준805CI39136943043의3.10job117703259929가 Pyright
  단계에서 ctypes.WinDLL2오류로실패했고 matrix3.12는취소됐습니다. 제품renderer/test실패나
  오래된budget문제로덮지않고 실패log와localLinux platform probe에서같은오류를확인했습니다.
- Windows branch에서cachefactory를추출할때ownplatformguard가빠져LocalWindows검사가
  이를드러내지못했습니다. Factory가non-Windows에서WinDLL접근전에명시OSError를내도록
 2줄guard를추가했습니다. 캐시binding/type·freshPID조회/CloseHandle·원래Linux reader는
  그대로며 cast/ignore/suppression/dependency변경은없습니다.
- GlobalPyright를Linux/Windows target각각0오류로검사했고 sampler/history4통과/1skip·
  Ruff230/format·계약·packaging7명령이exit0, 변경2경로LSP clean입니다. Skip은로컬Windows의
  새non-Windows runtimeguard이며 실제Linux실행은다음CI가필요합니다. 기존Win반복20sample
  타입재사용은계속통과합니다. 현재실패를새성공결과로바꾸거나CI-01을닫지않습니다.
- Layout 검증은이실패보다우선하지않고이번단위에서는수정하지않았습니다. 남은baseline
  job을임의취소하지않고 도구hotfix를로컬보존한뒤완료상태에따라게시합니다. 원문/버전/
  의존성/lock/tag/배포·상태개수·loop1은유지합니다.

## 35차 — HTML/SVG data·명시 PGF TeX 문자열 문맥

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-string-boundary-_1kovvmy`와
  [문자열 경계/현재 경고 분류](review_evidence/string_boundary_verification.json)를 보존합니다.
- &,<,>,따옴표,backslash,Ω·무해script문자열의 HTML attribute/draft JSON은 한번 decode해
  원문/spec와 같고 trustedscript본문은늘지 않습니다. SVGtext-mode XML도 원문과href를
  유지하고 script/event node가 생기지 않았습니다. 양실제editor GETHTML의4payload회도
  attribute/state가같고script가변하지 않았습니다. Parser대조이지브라우저공격인증은 아닙니다.
- RawPGF A&B는명확한TeX측정오류이며 A\\&B·명시무해macro/math는실제pdflatex로
  컴파일됩니다. T1encoding과10inch그림을담는paper에서Poppler추출문자도 amp/hash/
  percent/underscore/backslash/inert/math를 유지합니다. Citation의brace/backslash macro는
  validation이거부합니다. PGFtext는신뢰TeX입력이라는기존정책을명확히하고 잘못된광범위
  plain-text-escape주석만고쳤으며 runtimeescaping/공개API/수식지원은바꾸지 않았습니다.
- 관련72case가skip없이통과·최소6통과/2945deselected/경고185·Ruff230/format·Pyright·
  계약·packaging7명령이exit0이며변경3경로LSP clean입니다. 별도 pytest warning hook으로
  현재185개가모두oldMatplotlib의font/mathparser PyparsingDeprecationWarning임을기록했습니다.
  Suppress/dependency pin은추가하지않고이subset으로과거전체3906개를분류하지 않습니다.
- OUT-09는이문맥/지원fixture에서PASS입니다. UntrustedTeXsandbox·모든Unicode/font/OS를
  보장하지않습니다. 초기draft_json생략/너무좁은OT1paper·잘못된pytesttemp이름가정은
  QAfixture/control문제로고쳐현재T1/fitted paper를다시실행했으며제품실패로세지 않습니다.
- 기준06dCI39131994074는이제5job모두성공했습니다. 후속도구/test는별도local검증이며
  대기하던sampler/출력단위와게시해새CI를받습니다. 버전/의존성/lock/tag/배포·loop1은유지합니다.

## 34차 — 실제 출력 metadata·PGF bundle·문서 참조

- 로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-output-reference-45nnpl7g`와
  [출력/참조/폰트/URI 요약](review_evidence/output_reference_verification.json)을 보존합니다.
- Reference를 가진 동일 spec의 PNG/PDF/SVG를 시간 간격·새 process로 반복해3hash가
  각 형식에서 같았습니다. PDF CreationDate/ModDate·SVG dc:date는 없고 SVG ID는 unique/
  결정적이며 DOI href/라벨은 남습니다. PNG/nativePDF는 plain label, SVG는link/citation
  key비노출, PGF는문서가 figcite/href를 해결하는 정책을 지켜 OUT-02/07은 PASS입니다.
- 새 PGF2회귀는 원래 basename의 상대 sidecar를 함께 옮기면 실제 pdflatex 컴파일이
  성공하고 PGF만 옮기면 nonzero가 되는 것을 확인합니다. 후처리 OSError에서Figure는
  닫히지만 원래PGF가 보존되지 않고 sidecar가 남는 현재 비트랜잭션 한계를 명시해
  OUT-06은 PASS입니다. 새 bundle transaction이나 기존 사용자 파일 실험은 추가하지 않았습니다.
- 전체 관련70case는 skip 없이 통과했습니다. Tectonic·pdflatex+bibtex·lualatex+bibtex·
  lualatex+biblatex의4실제 문서에서 citation번호/라벨을 확인했고 설치Poppler25.02.0의
  pdffonts/pdfinfo-url로각PDF의보고된5font embedded와DOI annotation도 확인해 OUT-08은
  이 installed matrix에서 PASS입니다. CJK/모든font/모든OS/TeX환경까지 보장하지 않습니다.
- 기존 network/shell/pickle 차단된 normalPNG/PDF/SVG reference3case도 통과했습니다.
  명시 trustedTeX tool/package 실행은 별도 경계입니다. Floor6통과/2939deselected/경고13·
  Ruff229/format·Pyright·계약·packaging6후속 명령도 exit0이며 새2경로LSP clean입니다.
  Compiler.log/.blg·JUnit70case·형식SHA·폰트/URI 출력 hash를 보존했습니다.
- Product runtime은 그대로이며 새 test/floor roster/doc만 로컬 commit해 진행 중06dCI를
  취소하지 않습니다. OUT-09전체문자경계·자원/권한·PGF atomicbundle의 미지원 범위는
  별도이며 버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 33차 — bounded 세션 자원·observer 자체 누수 분리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-session-resources-5uznsuts`,
  [RSS/객체/handle/cache 시계열](review_evidence/session_resource_verification.json)을 보존합니다.
- 500행·30history-growth+30fixed-history/open-replace cycle·실패 effect10회 등 최소
 240render의137.016초 관찰입니다. 15checkpoint에서 GC후 live/openFigure0·handle198·
  temp file0이었고 history는0→30, replacement에서는1, final reopen은0입니다. 캐시 PNG는
  마지막 한 그림20~21KB로 교체됐습니다. 장시간/모든OS 안정성 완료로 확대하지 않습니다.
- **FIND-031 (검증 도구):** GC 객체 증가를 renderer 누수로 먼저 단정하지 않고 sampler
  단독20회에서 Counter타입20개·객체662개 증가를 재현했고 새회귀1개가 실패했습니다.
  Windows ctypes POINTER cache가 함수 내부의 새타입을 보관하므로 binding/type만
  lazy-cache해 재사용했습니다. Sample값/PID handle을 cache하지 않으며 OpenProcess/
  CloseHandle·Linux reader는 유지합니다. 수정 후 warm대조 새타입0·객체증가2였습니다.
- 새sampler로 전체 cycle을 다시 실행했습니다. WarmRSS87,904,256→final96,428,032bytes,
  lifetimepeak246,550,528bytes이며 이는 native backend/cache/allocator도 포함하는 ownPID
  working set입니다. GC전 닫힌Figure는 collectable이고 history/측정 row 보관량도 구분합니다.
  RSS 증가만으로 native leak이 없거나 있다고 단정하지 않습니다. 기존 server-PID RSS를
  외부 observer에서 읽던 결과와 observer-own객체 증가는 같은 메모리 공간이 아닙니다.
- Related63통과/OS2skip·Ruff228/format·Pyright·계약·packaging6명령이 exit0이며 변경2경로
  LSP clean입니다. Product renderer/state를 바꾸지 않고 관찰 helper를 수정했습니다.
- PERF-04는 OPEN→RUNNING이며 더 긴 시간축/다른 workload·Rust child/native lifetime
  검증은 남습니다. 최초 잘못된 export(json)/mp.LayerSpec QA 접근은 실패/partial log로
  보존하고 제품 결함이나 완료 관찰로 세지 않습니다. 새단위는 진행 중06dCI를 끊지 않도록
  로컬 보존하며 원문/버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 32차 — owned Matplotlib effect 직렬화

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-concurrent-proof-wdl6qvz2`,
  [동시/단독 byte 비교](review_evidence/concurrent_render_verification.json)를 보존합니다.
- **FIND-030:** 서로 다른font/제목 그림의 동시 public PNG/SVG save2case가 serial
  bytes와 달랐습니다. 별도 rc/font 관찰1case는 현재 버전에서 통과했으므로 특정 font
  값/Matplotlib 내부 원인으로 단정하지 않습니다. Session별 lock만으로 전체 process의
  API/다른 session/preview effect를 격리할 수 없어 공통 경계를 추가했습니다.
- 새 stdlib-only RLock context는 APIrender/save·tex_preview·Python editor의 preview/
  placeholder/export·site/gallery effect를 직렬화합니다. 중첩 호출은 reentrant이며
  같은 session의 기존 state lock/반환 Figure 소유권은 유지합니다. Caller가 직접 하는
  Figure/pyplot/Store 조작·동일출력경로 경합·thread중fork·crossprocess는 보장하지 않습니다.
- Controlled2entrypoint interleaving·PNG/PDF/SVG3format의 서로 다른2그림 serial/
  concurrent byte/hash·독립 editor2session PNG/SVG/layout의6case가 통과했습니다.
  Core optional import를 앞당기지 않았고 NoDeps/TeX 중첩·실패 rollback regression도
  포함한 관련231통과·site9통과·실제floor6통과/2937deselected/경고13과8기록 명령이 exit0입니다.
  Ruff227/format·Pyright·계약·packaging·변경8경로 LSP clean이며 floor roster도 포함했습니다.
- PERF-06은 이 supported owned-call corpus에서 PASS입니다. 처리량 개선/임의Matplotlib
  thread-safe 인증은 아니며 직접 받은Figure는 함수가 끝난 뒤 caller가 조정해야 합니다.
  이전 failing raw는 harness 기록이고 처음 mp.apply 인수 순서 QA 오류도 성공으로 세지 않습니다.
- 현재31e의 full CI는 진행 중이므로 새 effect 코드가 이전 결과로 검증됐다고 하지 않고
  로컬 commit으로 보존합니다. 선언적core/state·버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 31차 — bounded rows×history와 worker RSS

- 실행: `uv run --no-sync python scripts/profile_history_costs.py`.
  로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-history-verified-9637jcvy`와
  [matrix/checkpoint 요약](review_evidence/history_cost_verification.json)을 보존합니다.
- 1천/1만/10만 행×10/100/1000 action의9조합을 독립 core-only child로 실행했습니다.
  Child12초·dispatch2.5초·RSS관찰512MiB 예산이며 OS hard memory/CPU 한도가 아닙니다.
  총6개 목표 완료·3개 조합은 시간 예산에서 중단됐고 실제 timeout/child failure/OOM은 없었습니다.
- 완료한1천×1000의 undo/redo는402.35/404.45ms,1만×100은336.30/339.29ms,
 10만×10은362.61/392.95ms입니다. 1만×1000은375action,10만×100/1000은39/38action에서
  멈춰 목표 미달이며 undo/redo는 null입니다. 중단 데이터를 성공한 목표나0ms로 세지 않습니다.
- 각 worker PID의 working set/lifetime peak를 기존 _memory helper로 읽었습니다. 최종
  측정 peak최대53,571,584bytes이며 초기 import/baseline 포함, renderer 자손·장시간
  GUI leak·동시성·모든 OS·cross-hardware latency 보장이 아닙니다. RSS handle은 기존
  helper가 정리하고 core-only timeout child도 수집기가 종료/reap합니다.
- 3회귀는 합성 timeout의 마지막 잘린 JSON/child 오류/잘못된 complete checkpoint에서
  앞선 단계와 unknown/null·원인을 보존합니다. 실제 OOM을 냈다는 뜻은 아닙니다.
  현재 matrix와 관련62통과/OS2skip·Ruff225/format·Pyright·계약·packaging6명령이
  exit0이며 새2Python경로 LSP clean입니다. Core/alias/replay 구조는 바꾸지 않았습니다.
- PERF-02는 이 bounded matrix에서 PASS입니다. 미완료 셀은 extrapolate하지 않고
  snapshot 안전성/기존 checkpoint shortcut을 유지합니다. label 경로도 정적 확인상 이미
  None/empty를 구분해 불필요하게 고치지 않았습니다. 새 script/doc은 진행 중인31e CI를
  취소하지 않도록 로컬 보존하며 원문/버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 30차 — 명시 빈 marker/style의 의미 보존

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-render-token-probe-r9gzppx_`,
  [token 의미 대조](review_evidence/render_token_verification.json)를 보존합니다.
- **FIND-029:** schema/JSON이 보존한 marker/line_style 빈문자열을 renderer가 자동값으로
  바꾸던6artist case를 재현했습니다(동일 초기사례2개는 통과). 공통 renderer는 None만
  fallback하고 명시 empty no-marker/no-line을 유지합니다. Non-line None의 자동 circle·
  기존 marker size0/null/기존 layer별 지원 제한은 유지하며 새로운 public API는 없습니다.
- 추가13artist case와 기존27size/null/zero 의미를 대조했습니다. Compact shared fixture는
 5layer/field×omitted/null/empty/explicit20case이며 schema/Python·실제 CLI migrate parser/
  I/O·5fresh moduleCLI PNG render·Rust strict typed codec·Python 재로드를 확인했습니다.
  양 editor rawJSON/HTMX open/spec/PNG40회가 직접 Python 결과와 같습니다. Omitted→
  PythondefaultNone 정규화는 허용하지만 값/타입을 덮어쓰지 않습니다.
- Fixture의 중복 full spec은134287→19307bytes로 줄이고 canonical equality20개를
  확인한 뒤 compact input UI40회도 다시 통과했습니다. 모든139nullable field/자동값/
  visual dropdown을 검증한 것은 아니므로 JSON-09는 RUNNING입니다.
- 관련266통과/단일 관측 pointplot interval 경고2·최소79통과/2858deselected/경고15,
  native lib21+main1통과/helper6ignored·Ruff223/format·Pyright·계약·packaging10명령이
  exit0입니다. 새LSP3경로는1clean/2inconclusive이며 globalPyright0을 별도로 기록합니다.
- 초기 잘못된 HTML id=app 가정은 Python inner app-body 계약을 읽고 수정한 QA 제어
  실패이지 제품 결함이 아닙니다. AST rule backend 부재에 package를 설치하지 않았고
  알려진 identifier 검색으로 caller를 확인했습니다. 소유 서버는 각 시도 뒤 정리했습니다.
- 기준ea1CI39125371498은 이제5job 전부 성공했지만 새 renderer 수정 이전 결과입니다.
  완료된 baseline을 더 기다리지 않고 로컬 성능 단위와 이번 수정을 함께 게시해 다음 CI를
  받습니다. CI-01/JSON-09 상태와 버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 29차 — 편집/직렬화/렌더 비용 측정·자손 정리 원격 확인

- 실행: `uv run --no-sync python scripts/profile_state_costs.py`.
  로컬 증거 `C:\Users\mud\AppData\Local\Temp\mudplot-state-profile-e02g_zfu`와
  [성능 요약](review_evidence/performance_verification.json)을 보존합니다. Synthetic3열
  1천/1만/10만 행·4x3inch/72DPI·warm 경로이며 core20회/render10회·nearest-rank p95입니다.
- Title dispatch median/p95(ms)는0.803/0.841,6.993/7.687,67.867/69.090입니다.
  같은10만 행 JSON encode174.954/177.742·decode182.815/186.273,
  model→figure/close503.747/507.971·전체 PNG save/close533.225/554.047입니다.
  첫 import/font discovery·cold process/장기 이력·동시성·native RSS/SLO는 아닙니다.
- 별도10action/1noop listener cProfile7.783초 중 deepcopy누적7.777초(99.923%)이며
  render/validation 호출은0입니다. 계측 overhead가 실제 dispatch latency와 다르고 public
  pstats 시간은 ms 반올림입니다. 별도1dispatch tracemalloc peak4,828,472bytes는 Python
  할당일 뿐 RSS가 아닙니다. Counting listener21회·data/spec 보존·Figure 정리도 assert했습니다.
- PERF-01/03은 이 측정 범위에서 PASS입니다. Snapshot alias 안전성을 유지하며 immutable/
  zero-copy rewrite·validation 제거·장기 이력 checkpoint를 근거 없이 추가하지 않습니다.
  초기 QA script의 잘못된 mp.SetTitle 접근은 성공 측정으로 세지 않았으며 기존 mp.actions로
  수정했습니다. 관련59통과/OS2skip·Ruff223/format·Pyright·계약·packaging6명령이 통과했습니다.
- [현재 자손 정리 원격 근거](review_evidence/remote_cleanup_verification.json)도 확인했습니다.
  정확한ea1 소스에 Linuxjob117669271500(lib19+main1통과/helper5ignored), Windowsjob
 117669271625(lib20+main1통과/helper6ignored)의 controlled descendant와 MSRV step이
  성공했습니다. Windows 정리 도구 부재/복구도 성공해 RUST-04는 이 foreground policy에서
  PASS입니다. Detached/reparented/hard-resource 경계는 유지합니다.
- Full Python/floor CI는 여전히 실행 중이므로 CI-01은 RUNNING이며 이 새 script/doc은
  로컬 commit으로 보존합니다. 제품 core·버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 28차 — foreground 자손 timeout 정리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-descendant-lj9xrjfm`,
  [child tree·정리 실패·복구 요약](review_evidence/descendant_cleanup_verification.json)도 보존합니다.
- **FIND-028:** controlled parent의2초 timeout 뒤 직접 child는 끝났지만 추가 child가
 4초 완료 marker를 계속 기록하는 회귀1개가 수정 전 실패했습니다. 실패 raw는 harness
  기록이며 이 폴더의 성공 receipt로 꾸미지 않습니다. 실제120초를 기다리지 않았습니다.
- 공통 run에서 Unix child에 새 process group을 주고 timeout/wait 오류 때만 보유 PID에
  대응하는 group을 /bin/kill로 정리합니다. Windows는 SystemRoot/System32 taskkill의
  /T/F로 소유 tree를 정리합니다. Shell 문자열/PATH 탐색/다른 interpreter 대체는 없습니다.
  Cleanup command는 null stdio·별도2초 예산이며 직접 child kill/reap도 시도하고 정리
  실패는 원래 오류에 남깁니다. Detached/reparented worker는 지원하지 않는 명시 한계입니다.
- Windows에서 descendant marker가 남지 않고 다음 child가 성공했습니다. 별도 child의
  SystemRoot만 잘못 지정한 정리 도구 부재도 진단에 남기고 직접 child 종료/후속 성공을
  확인했으며 전역 환경을 바꾸지 않았습니다. 기존100ms stub은 cleanup 예산을 반영한
  유한4초 관찰 한도로 유지하며 제품120초/HTTP16MiB는 그대로입니다.
- 현재 local native lib20+main1통과/helper6ignored·Clippy/fmt·build와 정상 실제 bridge/
  HTTP path 집중 smoke가 통과했습니다. Ruff222/format·Pyright·계약·packaging9명령은
  exit0이고 변경Rust LSP clean입니다. Local compiler는 stable만 설치되어 새MSRV/Unix
  실행으로 세지 않으며 RUST-04는 다음 CI 전 RUNNING입니다.
- 기준e728CI39122032427은 이제5job 모두 성공했지만 이번 runtime 변경 이전 결과입니다.
  새 cleanup code로 소급해 CI-01을 닫지 않습니다. 완료된 기준 실행을 더 기다리지 않고
  로컬 privacy/원격증거 단위와 이 수정을 함께 게시해 다음 원격 검증을 받습니다.
  버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 27차 — 실제 Linux floor·양OS native 완료 증거

- CI39122032427/e728의 minimum job117659400040은11:08:28Z→11:25:16Z에 성공했습니다.
  [원격 floor 요약](review_evidence/remote_floor_verification.json)과 로컬 raw log
  `C:\Users\mud\AppData\Local\Temp\mudplot-ci-floor-proof-0no59qr_`를 보존합니다.
- 정확한 checkout SHA와 Python3.10.22/NP1.23/MPL3.8/SM0.14.1/SciPy1.10 banner,
  ordered60파일 완료 결과를 확인했습니다: **2872통과/26skip/경고3906,943.69초**입니다.
  Skip은 pyarrow/polars 선택 adapter25개와 biber1개뿐이며 새 staging symlink skip은
  없습니다. 경고 category는 --disable-warnings로 이 log에 없으므로 무해하다고 분류하지 않습니다.
- e728의 정확한 parametrize 소스·전체 성공·완전한 skip 요약을 함께 읽어 staging4symlink
  case 통과를 판단합니다. 개별 verbose case 로그가 있다는 주장은 아닙니다. Current
  io/output-test/corpus/native-helper/floor-script가 그 commit과 같음을 비교했습니다.
- 양OS Rust job117659399818/117659400047도 성공하며 각각 lib18+main1통과/helper3ignored,
  Host/Origin/16MiB/path/header 회귀 통과를 실제 완료 log에서 확인했습니다. Windows
  파일/directory/hardlink·이전 경로 probe와 함께 SEC-06은 이 관찰 범위에서 PASS입니다.
  적대적인 shared-directory sandbox/모든 OS·경로·자손 정리 보장으로 확대하지 않습니다.
- Full Python3.10/3.12는 여전히 실행 중이므로 CI-01은 RUNNING이며 새 privacy-only
  회귀를 이 원격 floor가 실행한 것으로 소급하지 않습니다. 이번에는 runtime/test 코드를
  바꾸지 않고 증거/status만 로컬 보존해 진행 중인 CI를 취소하지 않습니다.
- 최초 gh log fetch의 escape 거부와 private source decode의 잘못된 Windows 기본 인코딩은
  제어/취득 실패로 남깁니다. --allow-escape-sequences/UTF8로 완료한 읽기만 근거이며 테스트
  실패/성공으로 집계하지 않습니다. 버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 26차 — 기본 오류 로그·현재 lock advisory 검토

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-private-errors-wb54fsyh`,
  [민감값 probe/lock 조회 요약](review_evidence/privacy_audit_verification.json)도 보존합니다.
- 합성 token/연구 행만 사용해 실제 Python/Rust 서버의 invalid action/import/render/
  unknown-route 오류를 주입했습니다. 기본 stdout/stderr에 marker나 traceback이 없고
  spec/PNG는 보존됐습니다. 같은 client UI가 오류/draft/current state를 반환하는 편집
  경로와 server log를 구분하며 무조건 입력을 지워 편집을 깨뜨리지 않았습니다.
- Python HTTP의 기본 log 비노출 회귀1개를 추가했습니다. 관련211통과·실제 최소1통과/
  2898deselected/경고13·Ruff222/format·Pyright·계약·packaging7명령이 exit0이며 변경
  test LSP clean입니다. 제품 runtime/log 정책 코드를 바꾸지 않았습니다.
- `audit_dependencies.py`의 root/all-extras·minimum·audit 세 Python lock export에
  알려진 취약점이 없었습니다. 추가로 official OSV querybatch에 Cargo registry69개
  name/version만 보내 advisory0을 확인했습니다. Local crate 제외·git/private source
  없음도 확인했습니다. cargo-audit binary를 실행한 것은 아니고 unmaintained/license/
  모든 platform·후속 설치환경 범주까지 검사했다고 표현하지 않습니다.
- 현재 조회 결과와 기본 logging scope를 적용성/한계와 함께 기록해 SEC-08은 이
  관찰 범위에서 PASS입니다. Actual credential/research data를 사용·기록하지 않았고
  clean 결과를 보안 인증으로 표현하지 않습니다. Debug/custom observer/proxy/명시CLI
  출력·외부 dependency resolution은 별도 검토이며 security 문서에도 명시했습니다.
- 새5job CI는 실행 중이므로 이 test/doc 단위는 로컬 commit하고 원격을 취소하지
  않습니다. 원문/버전/의존성/lock/tag/배포·loop1은 그대로 유지합니다.

## 25차 — full/floor CI 실행 예산 분리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-ci-floor-lxto_ug4`,
  [동일성/runner/부분 실행 요약](review_evidence/ci_floor_split_verification.json)도 보존합니다.
- **FIND-027 (CI 배치):** full Pytest 성공 뒤 최소환경이 남은 job 시간을 쓰다 취소된
  기준621의1h annotation을 근거로 floor를 독립 Linux/Python3.10 job으로 옮겼습니다.
  Full3.10/3.12는 그대로이며3Python job 각60분·양Rust 각20분의 유한 예산입니다.
- Ordered floor TESTS60파일과 PEP723 의존성/lock·기존 not-browser filter는 바뀌지
  않았습니다. Pdflatex/tectonic 설치 본문·고정 version/checksum hash가 이전과 같음을
  비교했고 같은 locked tooling/Playwright install-deps로 font/system 전제도 유지합니다.
  Floor만을 위한 browser binary는 받지 않으며 full matrix의 browser 검사는 유지합니다.
- Floor에도 느린25개 timing을 출력하고 runner가 모든 파일과 pytest 실패 반환값을
  전달함을 검사했습니다. 새 guard는 수정 전 실패·수정 후 CI/릴리스 계약7통과입니다.
  실제 핵심 floor39통과/권한4skip/2855deselected/경고13과 Ruff222/format·Pyright·
  계약·packaging7명령이 exit0, 변경3경로 LSP clean입니다. 전체 floor와 새로운 Linux
  apt/font setup·5job 원격 실행 성공은 아직 아니므로 CI-01은 RUNNING입니다.
- 이번에는 개별 검사/보안 한도·Native120초·HTTP16MiB·버전/의존성/lock/tag/배포를
  바꾸지 않습니다. 로컬 queue의 staging 소유권 수정/문서와 함께 게시하고 다음 원격
  결과로 job 분리 효과와 추가 timing을 확인합니다. Loop1은 계속 유지합니다.

## 24차 — staging 소유권·HTTP 경로·offline sink

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-file-sinks-_n7m1pz3`.
- **FIND-026:** 강제 nonce 충돌4case에서 JSON 실패 cleanup이 기존 파일을 삭제하고
  PNG/PDF/SVG가 덮어쓰는 것을 재현했습니다. 공통 atomic helper에서 cleanup 범위 전에
  exclusive touch로 소유한 entry를 예약하고 text writer는 그 파일에 쓰도록 바꿨습니다.
  기존 text partial-write 주입도 실제 writer mode에 맞췄습니다. 기존 파일·directory·
  hardlink 보존12case가 통과하며 symlink4case는 Windows 권한으로 skip입니다.
- PythonHTTP는10개 ..·percent/double-encoded·backslash·NUL·알 수 없는 static 경로를
  거부하고 export query가 server output path를 선택하지 못함을 확인했습니다. 같은
  corpus의 native focused helper도 기존 Host/Origin/16MiB/header/state 보호와 함께
  통과했습니다. Static route는 Python 고정 bytes/Rust include_bytes+고정 router이며
  임의 server file 경로를 만들지 않습니다. Local export 경로는 sandbox로 제한하지 않았습니다.
- JSON→dataclass/metadata→reference 정규화→href/citation validation→기본 renderer를
  추적했습니다. DOI/arXiv/url·객체복원처럼 보이는 JSON·code처럼 보이는 label에서
  PNG/PDF/SVG의 socket/urllib/os.system/subprocess/pickle sink 시도가0이고 잘못된
  href scheme/TeX citation escape는 거부해 SEC-07은 이 supported corpus에서 PASS입니다.
  Backend/font 초기 discovery 뒤 입력별 audit를 적용했으며 명시 TeX/PGF의 신뢰 경계는
  별도입니다. Security 문서는 shared-directory/PGF bundle/임의Python sandbox를 보장하지 않습니다.
- 관련128통과/OS6skip·최소80통과/권한4skip/2814deselected/경고13과7기록 명령이
  exit0입니다. Ruff222/format·Pyright·계약·packaging 통과, 변경Python6경로 LSP clean입니다.
  SEC-06은 새 POSIX symlink 실행 등 후속 확인을 남겨 RUNNING으로만 올립니다.
- 기준621CI39115133320은3.12/양Rust 성공이지만3.10은1h job 한도 초과로 취소됐습니다.
  Annotation117639290243을 확인했고 Pytest는36분에 이미 성공, 다음 최소환경 step이
  남은23분을 쓰다 취소됐습니다. 테스트 실패·전체 green으로 세지 않습니다. 다음 단위에서
  최소환경 job 분리 등 전체 검사를 유지한 실행 구조를 검토하며 이번 소유권 수정은 로컬
  commit으로 먼저 보존합니다. 버전/의존성/lock/tag/배포·loop1은 유지합니다.

## 23차 — Windows 긴 TMP의 interpreter/capture 분리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-longtmp-epe7glbh`,
  [해시/12대조/bridge control](review_evidence/windows_tmp_boundary_verification.json)도 보존합니다.
- 긴TMP 실패를 제품/OS/capture 중 하나로 먼저 단정하지 않고 print/capabilities·pipe/file·
  base/venv·site on/off·TMP/TEMP 분리의12case를 각각6초로 제한했습니다. Short63문자
  control은 성공했고321문자TMP의 관찰 venv는 print도 시작하지 못해5case를 종료했습니다.
  이 종료 exit1은 성공이나 application 오류가 아니라 fixture timeout/정리 결과입니다.
- Base Python은 긴TMP에서 성공했고 venv의 -S는 차이가 없었습니다. 긴TEMP만 두고
  TMP를 짧게 하면 같은 venv도 동작했습니다. 따라서 mudplot/capture/site와 독립적인
  관찰 interpreter 시작 경계를 분리했으며 특정 uv/CPython 내부 원인·보편 임계값을
  새 제품 결함으로 주장하지 않습니다. Runtime 코드/OS 설정/자동 interpreter fallback은 없습니다.
- 같은 선택 venv와 shortTMP/longTEMP에서 실제 bridge 시작/open/action/PNG·한글
  metadata·336문자 입력 source 보존·long-directory 불변이 통과했습니다. 앞선PowerShell7.6.7/
  LongPathsEnabled1의93/336문자 API/CLI/lock 결과와 함께 지원 host 경로와 설정 한계를
  분리해 PKG-06은 이 관찰 범위에서 PASS입니다. 긴CWD/모든TMP 보장이나 RUST-04
  일반 자손 정리 완료로 확대하지 않습니다.
- 각 timed probe는 보유 PopenPID의 자기 tree만 taskkill/T/F 후 communicate했고 현재
  fixture 프로세스가 없음을 확인했습니다. 정상 endpoint 완료 뒤 소유 서버도 정리했습니다.
  제품 shutdown/timeout가 같은 보장을 한다는 뜻은 아닙니다.
- 최종 관련47통과·Ruff221/format·Pyright·계약·packaging6명령이 exit0입니다. Source/
  interpreter launcher/log/새 doc hash를 보존하며 새 전체/minimum/browser/nativeunit/OS
  suite는 아닙니다. 기준621CI가 실행 중이라 문서 단위는 로컬 commit으로 보존하며
  loop1·버전/의존성/lock/tag/배포 상태는 유지합니다.

## 22차 — lock/격리 build·matching source 편집기 실행

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-isolation-8zpvxkk4`,
  [격리/source-editor 요약](review_evidence/isolation_source_editor_verification.json)도 보존합니다.
- 별도 `UV_PROJECT_ENVIRONMENT`의 실제 `uv sync --locked --extra dev`43package가
  lock 버전과 일치했고 같은 명령 반복 후 버전 snapshot도 같았습니다. 기존 개발 venv/
  lock은 바꾸지 않았습니다. 이전 fresh 범위 설치의 NP2.5.4/MPL3.11.2 등과 현재 locked
  NP2.5.2/MPL3.11.1 등16차이를 구분해 lock을 모든 사용자 설치 보장으로 설명하지 않습니다.
- 비어 있는 private cache에서 PEP 517 격리 wheel을 sdist로부터 만들었습니다.
  verbose log가 별도 build env와 Hatchling1.32.0을 확인했고 전이 build package는
  pluggy1.7/tomlkit0.15.2 등으로 dev lock과 구분됩니다. 현재 환경 build와 관찰한
  wheel55member/바이트/SHA가 같지만 다른 환경의 byte-identical을 보장하지 않습니다.
- 그 wheel을 또 다른 무의존 consumer venv에 설치해 저장소 밖 core/schema/validate/
  JSON·NumPy/dashboard 부재와 package source를 확인해 PKG-09는 이 범위에서 PASS입니다.
- Matching621 source/artifact snapshot의 locked Python으로 실제 문서 command형태
  dashboard serve와 cargo run editor를 시작했습니다. HTML/spec/PNG·공유htmx SHA·
  라이선스·Python/docs route가 통과하고 소유 process tree를 끝내 PKG-08은 PASS입니다.
  Released tag나 standalone editor 배포를 승인·생성했다는 뜻은 아닙니다.
- **FIND-025 (문서):** Rust README의 'Linux CI 미관찰' 문구는 기준e14의 실제 양OS
  성공과 맞지 않아 해당 commit/run 범위를 적었습니다. 양 editor README는 wheel에 UI/
  source asset이 없음을 명시하고 기여 가이드는 locked/허용범위/격리 build를 구분했습니다.
  이번에는 제품 runtime 코드를 바꾸지 않았습니다.
- 관련12통과·Ruff221/format·Pyright·계약·최종 packaging6명령이 통과했습니다. 별도
  locked/isolated 3receipt·verbose/반복/동일성/consumer/editor 결과도 보존했습니다.
  새 전체/minimum/browser/nativeunit/OS 결과로 확대하지 않으며 CI621의 진행 중인
  실행을 취소하지 않도록 로컬 commit하고 게시를 보류합니다. 버전/의존성/lock/tag/배포는 유지합니다.

## 21차 — 설치 wheel·extras·외부 CLI 경계

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-installed-hvei5uef`,
  [설치 matrix/경로 제한 요약](review_evidence/installed_matrix_verification.json)도 보존합니다.
- **FIND-024:** core6surface와 color-only CLI/adapter3surface가 설치 extra 안내 없이
  missing-module만 내던 회귀를 재현했습니다. 기대한 numpy/matplotlib/cycler 부재만
  해당 effect 경계에서 ImportError 안내로 바꾸고 다른 transitive/compiled 오류는 그대로
  유지합니다. Figure 저장 후 기존과 같이 close하고 core import/기본 의존성은 바꾸지 않습니다.
- 실제 sdist→wheel을 새 uv venv에 설치한 뒤 core→color→render→cluster→regression→
  dev→browser의 **7점진 단계**를 검증했습니다. 서로 다른7venv라는 주장이 아닙니다.
  단계별 installed 패키지/모듈 부재·색 계산·PNG/PDF/SVG·고급 효과를 확인했습니다.
  Browser package와 비어 있는 browser-binary 경로의 별도 설치 안내를 구분해 PKG-02는 PASS입니다.
- 저장소 밖7명령×2진입점×7단계=**98CLI**에서 stdout/stderr/exit가 같고 예상 optional
  오류·기존 출력 보존도 확인해 PKG-04는 PASS입니다. Wheel5package파일·실제 설치파일·
  현재 source bytes가 일치합니다. 허용 범위 최신 의존성은 NP2.5.4/MPL3.11.2/SciPy1.18.1/
  statsmodels0.15/pandas3.0.6/Playwright1.64이며 project lock을 바꾸지 않았습니다.
- 4점 robust positive fixture는 정당한50iteration 수렴 오류였습니다. 실패 receipt를
  보존하고 기존40점 sinusoidal test 데이터로 설치 성공을 확인했으며 제품 한도를 완화하거나
  추가 제품 결함으로 세지 않습니다. 새 최소 extra 오류 회귀11개와 관련82개도 통과했습니다.
- PowerShell7.6.7·LongPathsEnabled1에서93/336문자 파일 경로, 한글/공백/괄호/&·상대/
  절대 API/console/module 저장·실제 exclusive lock 거부·출력 보존·staging 정리·해제 후
  복구·PNG가 통과했습니다. 긴 CWD의 console 시작 실패는 별도 보존합니다. 긴TEMP native
  bridge는40초 ready budget 내 확인되지 않아 통과로 세지 않았고 검증한 자기 fixture
  process tree를 정리했습니다. 원인 미확인·자손 정리 보장 미완료로 PKG-06은 RUNNING입니다.
- 최종 관련82통과·최소11통과/2833deselected/경고13·Ruff221/format·Pyright·계약·
  packaging의7기록 명령은 exit0입니다. Source7hash/최종 matrix·artifact hash도 보존합니다.
  LSP6경로는5clean/1inconclusive이며 새 전체/native/browser-binary/Linux/macOS/보안감사
  성공으로 확대하지 않습니다. PKG-07도 이번 Windows 결과만으로 닫지 않습니다.
- 기준e14 CI39111782233은 Python3.10/3.12·Rust Linux/Windows **4job success**입니다.
  이는 해당 commit의60분/전체 검사 통과이며 후속 optional 안내 변경을 소급 검증하지 않습니다.
  CI-01은 후속 실행 전 RUNNING·CI-07은 DEFERRED, 버전/의존성/lock/tag/배포는 유지합니다.

## 20차 — optional 의미·손상 JSON 복구·CI 시간 진단

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-json-semantics-harf1qd7`,
  [139필드 표/입력 행/실행 요약](review_evidence/json_semantics_verification.json)도 보존합니다.
- **FIND-022:** 허용된 marker size0이7개 경로에서 기본6/4로 바뀌고3D line이 지정
  크기도 무시함을9실패/18통과로 재현했습니다. 7truthy fallback을 None 검사로 바꾸고
  3D line에도 markersize를 전달했습니다. 생략/null 기본은 유지하며9종×3값27artist
  사례가 JSON 왕복 뒤 실제 크기를 확인합니다. 지원 외 새 style 옵션은 추가하지 않았습니다.
- Nullable139필드의 schema/Python 생략·null·명시 default·적용 가능 scalar0/false를
  확인했습니다. StatSpec.errorbar 기본ci와 LayerSpec.inner 기본legacy는 null과 다릅니다.
  전 필드 CLI/Rust/UI 의미 대조까지 끝난 것은 아니므로 JSON-09는 RUNNING을 유지합니다.
- API/CLI의 잘린 JSON·잘못된UTF-8·깊이3000·2만배열을 제한 child에서 확인했습니다.
  CLI 실패는 기존 출력 bytes를 보존하고 다음 migrate가 성공했습니다. NativeHTTP는
  26/30/6042byte 손상 입력을422로 거부해 spec/PNG를 보존했고188936byte 정상2만행을
  무손실 처리한 뒤 정상 편집도 성공하여 JSON-12는 이 관찰 범위에서 PASS입니다.
- Nullable/marker/CLI249통과·연결 render169통과, 최소174통과/2659deselected/경고13,
  nativechecker18출력/입력경계, CIguard2통과입니다. 최종 Ruff220/format·Pyright·계약·
  packaging도 통과했습니다. 원래9명령 중 native 도중 총240초 시도는 완료 결과로
  세지 않았고 선행3receipt를 보존한 뒤 별도 제한 배치에서 재검증했습니다. CI추가4검사도
  별도 source hash로 보존했습니다. LSP4경로는3clean/1inconclusive이며 기존 QA FP1건은
  분류를 유지합니다. 새 전체/browser/nativeunit/양 OS 실행 성공을 주장하지 않습니다.
- **FIND-023 (CI 구성):** 기준063의39108112974가 완료됐고3.12/양Rust는 성공,
  3.10은45분 한도 초과로 cancelled였습니다. Check117618247815 annotation의
  `The job has exceeded the maximum execution time of 45m0s`로 원인을 확인했습니다.
  다른 과거 취소 원인까지 소급하지 않습니다. Python job만 유한60분과 `--durations=25`로
  조정해 테스트 삭제 없이 다음 실행을 측정합니다. Static guard는 수정 전 실패/후2통과지만
  수정 후 remote 성공은 아직 아닙니다. CI-01은 RUNNING·CI-07은 DEFERRED입니다.
- 기준 실행이 끝났으므로 로컬cf95b78과 이번 수정의 게시를 재개합니다. 원문/버전/의존성/
  lock/tag/배포는 유지하고 남은 P1/P2·전체 v1 완료로 확대하지 않습니다.

## 19차 — 코어 결정성·참조 index·효과 경계

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-core-3cmovymj`,
  [경로 제거 코어 요약](review_evidence/core_boundary_verification.json)도 보존합니다.
- **FIND-021:** RemoveLayer/SetColorbar/SetLayerAt의 bool index가 실제0/1 layer를
  선택하거나 다른 noninteger가 내부 TypeError로 새는 것을18case 불일치로 재현했습니다.
  기존 범위 검사에 plain int 조건3줄을 더해 공통 reducer에서 거부하며 실패 뒤 state/
  action/history와 정상 복구를 확인했습니다. 기존 positive panel 자동 확장은 바꾸지 않습니다.
- 새 프로세스의 CWD·clock·hash/RNG seed0/97과4theme 교차 호출에서 정규화 상태
  SHA가 `5856fa6c…cc0171`로 같고 RNG가 변하지 않았습니다. 실제 이전 그림의 render/style도
  reducer 결과를 바꾸지 않아 STATE-07은 PASS입니다.
- Negative/out-of-range/bool/float/string/null layer index와 잘못된 panel·wire type,
  없는 column/matrix 참조를 확인했습니다. 임시 invalid spec을 순수하게 조립하는 정책은
  유지하고 validate/render 오류는 같아 STATE-08은 PASS입니다.
- Audit/import guard로 core의 data-file/write/network/subprocess·선택 의존성을 차단해
  schema/capabilities/validate/reduce를 실행해 STATE-09는 PASS입니다. Python code의
  readonly.py/.pyc import만 허용하며 초기 잘못된 code-open 차단은 QA를 고쳤습니다.
  Interpreter/package code loading과 임의 사용자 Python method sandbox를 보장하는 것은 아닙니다.
- 신규35case와 연결된 대상 **195통과**, 실제 최소 stack **35통과/2628deselected/
  경고13**입니다. Ruff220/format·Pyright·계약·clean packaging까지7명령 exit0,
  changed Python2경로 LSP clean이며 min runner에 신규 파일도 포함했습니다.
  새 전체/browser/native/양 OS 실행 결과로 확대하지 않습니다.
- CI는 `cancel-in-progress: true`이므로 기준063의 실행을 반복 push로 끊지 않도록
  이번 게시를 해당 실행 완료까지 보류합니다. CI-01은 아직 RUNNING이며 원문/버전/의존성/
  lock/tag/배포는 그대로입니다. 남은 P1/P2를 완료로 간주하지 않습니다.

## 18차 — 실제 bridge 실패 주입·빈 산출물 commit 방지

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-bridge-faults-final-ifnu5yl2`,
  [경로 제거 실패 행렬 요약](review_evidence/bridge_fault_verification.json)도 보존합니다.
- **FIND-020:** exit0 child가 빈 PNG를 만들면 `/action`이200으로 상태를 commit함을
  수정 전에 재현했습니다. 공통 `render_format`에서 빈 bytes를 거부해 cache와 이력을
  바꾸기 전에 실패합니다. 기존 missing-file 오류·성공 stdout·지원 format은 유지합니다.
  비어 있지 않은 모든 손상 파일을 decode하는 검증이나 disk/CPU 상한은 추가하지 않았습니다.
- 별도 uv venv의 고유 `.pth`/module과 private fault 파일로 child를 주입했으며 global/
  프로젝트 환경·외부 sitecustomize는 덮어쓰지 않았습니다. Capabilities empty/JSON/nonzero3,
  성공 JSON+1MiBstderr1, action empty/JSON/nonzero/큰stderr/render실패/누락/빈PNG/
  실제 regression extra 부재8, 빈 PDF/SVG export2의 **14경계**가 통과했습니다. 각 action
  실패 뒤 spec/PNG/redo hash와 정상 편집 복구를 확인해 RUST-03은 PASS입니다.
- Optional fixture가 처음에 wire field `type` 대신 무시되는 `kind`를 쓴 것은 QA만
  고쳤으며 제품 결함으로 더 세지 않습니다. 기존 interpreter 선택4case·실제 prefix/argv/
  Unicode path 검사는 계속 유지하고 같은 checker를 양 OS CI가 실행하도록 유지했습니다.
- Controlled3초 stub에100ms private timeout을 적용하고 뒤 정상 child 성공을 확인했습니다.
  실제120초를 기다리지 않았지만 자손 소유권은 아직 전부 확인하지 않아 RUST-04는 RUNNING입니다.
- Native **lib18+main1통과/helper3ignored**, Clippy·fault checker·Ruff219/format·
  Pyright·계약·clean packaging까지 **8기록 명령 exit0**입니다. LSP 두 경로 중 Python
  snapshot의 미포착 JSON exception은 verification 실패를 숨기지 않으려는 의도라 해당
  ast-grep1건을 false-positive로 분류했습니다. 새 전체/browser/minimum/양 OS count는 아닙니다.
- 기준fe4449d의 CI39104961495는 양 Rust/3.12 성공,3.10 cancelled여서 전체 cancelled입니다.
  취소 원인은 확인하지 않았고 후속 empty-artifact 변경을 소급 검증하지 않습니다. CI-01은
  RUNNING·CI-07은 DEFERRED이며 버전/의존성/lock/tag/배포는 그대로입니다.

## 17차 — bridge stderr 제한·preview·실패 cache

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-bridge-c9w45r3t`,
  [경로 제거 bridge/preview 근거](review_evidence/bridge_preview_verification.json)도 보존합니다.
- **FIND-019:** 실패 child의1MiB stderr가 그대로 UI error에 들어감을 새 회귀1개 실패로
  확보했습니다. 실패 출력만 raw64KiB+1 확인 뒤64KiB로 자르고 표시를 붙입니다. 성공 stdout은
  그대로이며 stdout marker가 error에 섞이지 않았습니다. UTF-8 replacement가 표시 byte를
  늘릴 수 있고 임시 디스크/CPU·비밀 마스킹·전체 자손 격리의 hard bound는 아닙니다.
- Controlled missing executable로 apply/open/undo/redo/reset 모두 실패시켜 initial/spec/
  history/future/PNG/error/revision이 바뀌지 않음을 확인해 RUST-06은 PASS입니다.
  Native **lib17+main1통과/helper2ignored**이며 Clippy도 통과했습니다.
- 실제 HTTP preview는 두 방향에서 DPI499/500/501의6case를 실행해 각각1996/2000/
  capped2000px를 확인했습니다. JSON size/DPI·SVG points·PDF MediaBox는 변하지 않아
  RUST-05는 PASS입니다. 이는 실제 최종2000px 이상 전체 PNG render를 한 것은 아닙니다.
- 전체 smoke에 추가한 preview 호출을 포함한 foreground240초 시도는 timeout되어 통과로
  세지 않았고, 별도 소유 process에서 focused preview를 다시 실행해 결과·정리를 기록했습니다.
  7기록 명령(native tests/Clippy/preview/Ruff219/format/Pyright/wheel)은 exit0,
  LSP3경로는 clean입니다. 새 full/browser/minimum/양 OS 성공을 주장하지 않습니다.
- RUST-03의 empty/malformed 출력 전체 주입과 RUST-04 timeout의 모든 자손/자원 처리는
  아직 남아 두 항목은 RUNNING으로만 올립니다. 초기 발표한 다른 optional/path 항목도
  이번에 확인하지 않은 부분을 조용히 닫지 않습니다. 버전/의존성/lock/tag/배포는 유지합니다.

## 16차 — 혼합 그룹·데이터 경계·JSON 정책

- 기반b16f1de 위에서 수행했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-json-6kiccy6h`,
  [경로 제거 정책 요약](review_evidence/data_json_policy_verification.json)도 보존합니다.
- **FIND-018 (raw group):** `["1",1]`이 NumPy 문자열 추론으로 합쳐지고 None을
  넣으면 분리되는 것을 수정 전4fail/2pass로 확보했습니다. 공통 `_series_masks`의
  dtype을 object로 유지해 원래 값으로 비교합니다. Default Python numeric equality는
  `1`/`1.0`/`True`를 통합하고 explicit ordered의 typed key는 그대로입니다. Raw null과
  empty label의 legacy 정책/`str(key)` caption 중복 가능성을 문서화했습니다. DATA-04는 PASS입니다.
- 빈 raw와 통계 관측 부재/싱글턴 interval, raw 중복 x/행 순서와 lineplot 집계·sort를
  실제 artist/source/JSON으로 비교해 DATA-08/09를 PASS 처리했습니다. 과거 KDE/분포
  singular·constant 검사는 별도 테스트/최소 배치 근거를 유지하며 모든 미래 조합은 아닙니다.
- Known-version dataclass unknown key는 무시하고 data metadata는 보존하며 unknown
  version은 거부했습니다. Rust capability 소비자의 top/per-layer 추가 키 허용도 통과해
  JSON-08을 PASS 처리합니다. Whitespace/key 순서/Unicode 표기는 canonical hash가 같고
  data list 순서/1대1.0 타입 대조는 달라 JSON-10도 PASS입니다.
- Optional marker omission/null/0/default와 제한 child의 잘린/잘못된 UTF-8/깊이3000/
  유효 large-array2만개 복구는 확인했지만 전 필드/CLI/Rust 경로 전체는 아니므로 JSON-09/12는
  RUNNING으로만 올립니다. 제품 loader 정책을 schema 검증과 혼동하지 않습니다.
- 최종 관련 **291통과**, 최소 **61통과/2567deselected/경고201**, native **lib15+main1
  통과/helper1ignored**입니다. Ruff219파일/format·Pyright·계약·clean sdist→wheel까지
  8기록 명령이 exit0입니다. LSP는6경로 중4clean/2inconclusive로 전부 clean 주장하지 않습니다.
  새 전체/browser/양 OS 성공으로 확대하지 않으며 버전/의존성/lock/tag/배포는 유지합니다.

## 15차 — 지원 범위 P0 통합 검증

- 기준92238f3의 CI run39057547031은 Python3.10/3.12·Rust Linux/Windows 네 job 모두
  success였습니다. 이 원격 결과는 후속 QA 변경 이전 baseline으로만 기록합니다.
- 실제 로컬 optional 전체는 **3423통과/Windows조건2skip/경고1**, exit0/JUnit을 확보했습니다.
  이후 Matplotlib3.8 contour의 allsegs 중첩 API 차이는 public Path 좌표 검사로 고쳤고
  신규 P0 **72개**를 현재/최소 stack에서 다시 통과시켰습니다. 제품 수치 코드는 바꾸지 않았습니다.
  후속 QA 변경까지 포함한 새 단일 전체 실행이라고 확대하지 않습니다.
- 최소 환경 Python3.10.22/NumPy1.23.0/Matplotlib3.8.0/statsmodels0.14.1/SciPy1.10.0에서
  TESTS의53파일을 중복 없는8배치로 실행해 **2573통과/선택25skip/0fail/0error**를 확인했습니다.
  단일 순서 실행과 다르며 처음 중단된 minimum-full은 통과로 세지 않았습니다.
- [P0 통합 증거](review_evidence/completion_p0_verification.json)에 환경/backend/실제 font
  파일 hash·lock hash·Sharma 원본34쌍·독립 OLS/mean-CI·범주/그룹/y2 소속·비대칭 행렬
  xy/annotation·fresh-process PNG/PDF/SVG SHA와 물리 크기를 연결했습니다. 색 교정·기존
  default·명시적 tight 의미는 유지합니다. 고정 환경 결정성이지 모든 환경의 동일 바이트 보장은 아닙니다.
- 실제 sdist→wheel을 무의존 uv venv에 설치해 저장소 밖 core/schema/validate/JSON·console/
  module CLI를 실행했습니다. NumPy/Matplotlib/pandas/SciPy/statsmodels 부재와 import 목록,
  license/entrypoint/Requires-Dist·artifact SHA를 확인했습니다. ZIP 파일 존재만 본 결과가 아닙니다.
- 현재 audit의 세 lock graph는 known vulnerability 없음이며 Ruff216파일/format·Pyright·
  계약 sync·native unit15통과/helper1ignored·최종 clean sdist→wheel도 통과했습니다.
  별도 native-browser foreground240초 시도는 완료 receipt가 없어 통과로 세지 않습니다.
- 위 근거로 BASE-02/03/04, PLOT-01/02/03/04/06, STAT-01/02, COLOR-01/02,
  LAY-01/02, OUT-01, PKG-01/03/05를 관찰한 지원 범위에서 PASS 처리합니다.
  CI-01은 후속 변경의 새 통합 CI 확인 전 RUNNING이며, CI-07 exact publish/tag gate는
  버전·릴리스 유지 요청에 따라 DEFERRED입니다. 태그 생성/배포를 승인·실행하지 않았습니다.
- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-completion-mmo9xjlf`.
  Runtime `.pi/loops`는 사용자 실행 상태이므로 커밋/삭제하지 않습니다. 반복 Loop1은 계속 유지합니다.
  P1/P2와 vague broader-parity roadmap이 남아 있어 v1 전체 완료로 선언하지 않습니다.

## 14차 — 문서 이력·no-op·long replay와 원격 Rust 확인

- 기반781f3f5 위에서 기존 정책을 검증했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-history-final-5yqwup_o`,
  [경로 제거 이력/원격 job 요약](review_evidence/history_policy_verification.json)도 보존합니다.
- Python open/reset은 새 이력, Rust open/reset은 undo 가능한 snapshot이며 reset은 시작
  기본 문서로 돌아갑니다. A의 미저장 편집/future가 있는 상태에서 B를 열고 export·undo/
  redo·reset을 확인했습니다. Python 실제 파일 picker/다운로드에서 source A/B bytes는
  불변이고 현재 B/reset spec을 다운로드했습니다. 서버에 bound filename/별도 dirty-bit 기능은
  없어 새로 구현하지 않고 정책을 명시했습니다. HIST-04는 **PASS**입니다.
- Equal-value action도 event/snapshot을 기록하고 old redo를 지우며 Store listener와
  Python/Rust 이력 의미가 유지됐습니다. HIST-05는 **PASS**입니다. Seed20261016/24301의
  각768유효 action과128undo/128redo checkpoint에서 spec/cursor/hash가 정확히 일치하여
  HIST-06을 **PASS** 처리합니다. 무한 이력/성능 상한 또는 coalescing 최적화 주장은 아닙니다.
- **FIND-017 (Rust UI):** 서버 state는 맞아도 빠른 title/theme/history 요청의 outerHTML
  swap target이 분리되어 official htmx의 null querySelector pageerror가 발생했습니다.
  Root의 hx-disabled-elt로 요청 중 현재 control들을 비활성화해 중복 swap을 방지했습니다.
  Vendor/서버 정책은 바꾸지 않고 실제 reset/undo/redo click·CSP/pageerror 없음도 확인했습니다.
- 처음 native form-selector 가정은 실제 standalone hx-post button과 달라 QA만 고쳤습니다.
  첫 묶음은 history199통과 후 browser1fail/31pass에서 멈췄습니다. 파일 선택 뒤 Open
  section 재접힘을 재확인하는 테스트로 보강하고 최종 재실행했습니다. 이전 실패를 완료로 세지 않았습니다.
- 최종 **이력 대상199통과**, 전체 Python browser **32통과**, 실제 Rust HTTP/browser의
  문서/no-op/상태/PNG 시나리오 통과. 최소 **이력-only20통과/2506deselected/경고13**이며
  더 넓은 이전354case 반복이 아닙니다. Ruff213파일/format·Pyright·계약·clean sdist→wheel을
  포함한9기록 명령이 exit0입니다. 새 전체 application regression/native-unit count는 없습니다.
- 781f3f5의 CI run39050108296에서 Linux job117447100073와 Windows job117447100196은
  MSRV1.88·native tests·bridge smoke·interpreter 경로·본문/RSS 단계 모두 성공했습니다.
  그 근거로 RUST-02를 **PASS** 처리합니다. Python3.12도 성공했지만 Python3.10이 취소되어
  workflow 전체 결론은 cancelled입니다. 전체 CI/OS/릴리스 승인으로 확대하지 않습니다.
- 원문 체크리스트/의존성/lock/버전/tag/배포는 유지합니다. 현재 UI 수정은 별도 로컬 변경이므로
  원격781의 성공을 이 후속 변경의 CI 통과로 소급하지 않습니다.

## 13차 — 미지원 scalar 거부·가려지지 않는 probe 계측

- 기반914a402 위에서 진행했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-scalars-j2l4rnhk`,
  [경로 제거 scalar/계측 요약](review_evidence/scalar_provenance_verification.json)도 보존합니다.
- **FIND-015 (DATA-06):** Decimal NaN/일부 custom 객체의 self-inequality가 null로
  바뀌고 sNaN은 InvalidOperation, longdouble/새 same-type·순환 item은 RecursionError로
  끝남을 수정 전7fail/50pass로 확보했습니다. Missing 판정은 알려진 NumPy/pandas
  floating/temporal scalar에 한정하고 item은 지원 plain/date 표현일 때만 재귀합니다.
  정상 numeric/bool/Unicode/NaN/NaT·기존 item→기본값 변환은 유지합니다.
- 새71개 검사에서 mapping/records/object dtype의 값/타입·미지원 원객체 보존·strict
  JSON ValueError·비반사 custom 객체 비교/문자열화 방지·한 번만 수행하는 item·pandas
  NA/NaT를 확인했습니다. Unsupported extended precision을 float로 강제변환하지 않으며
  arbitrary Python method sandbox는 아닙니다. DATA-06은 이 범위에서 **PASS**입니다.
- 914a402의 CI run39048096708 Linux job117440805789는 MSRV/lint/unit과 advanced
  smoke를 통과했지만 경로 probe의 default.jsonl provenance가 없어 실패했고 Windows는
  취소됐습니다. 잘못된 interpreter 선택이나 실제 remote customizer 경로는 증명되지 않았습니다.
  **FIND-016 (QA 가정 보강):** venv sitecustomize lookup을 전제하지 않고 임시 전용
  module/.pth로 recorder를 로드합니다. 별도 shadow sitecustomize를 그대로 유지해도
  recorder가 실행됨을 self-check했고 원래 executable/prefix/version/argv assertion은 유지합니다.
- Optional overlay **244통과/skip0**, 프로젝트 대상 **1116통과/27skip**, 최소 대상
  **354통과/선택25skip/2142deselected/경고481**입니다. 실제 Windows 경로4case/
  12child와 foreign-customizer 보존도 통과했습니다. Ruff212파일/format·Pyright·LSP5경로·
  계약·clean sdist→wheel까지9명령이 exit0이며 새로운 browser/native-unit count나 Linux
  재통과로 세지 않습니다. RUST-02는 계속 RUNNING입니다.
- 프로젝트 의존성/lock·원문 체크리스트·버전/tag/배포는 유지합니다. 기존 실패 로그는
  ANSI 제거 후 읽어 SHA를 보존했으며 원격 CI 재실행은 후속 푸시 후 별도 관찰해야 합니다.

## 12차 — 커밋/푸시 후 timestamp 정밀도·CI 환경

- 6~11차 변경46파일을 `359277c6c7ee6862a85a158eb32ba9d4cf4dcf87`로 커밋하고
  origin/main에 푸시한 뒤 진행했습니다. 태그/버전/릴리스 상태는 바꾸지 않았습니다.
  현재 phase의 로컬 증거는 `C:\Users\mud\AppData\Local\Temp\mudplot-review-temporal-9n9cnwba`,
  [경로 제거 temporal/CI 요약](review_evidence/temporal_ci_verification.json)도 보존합니다.
- **FIND-013 (DATA-05):** NumPy datetime64 ns/ps/fs/as가 epoch 정수로 바뀌고 Polars
  ns가 microsecond로 잘리는 것을 수정 전36fail/16pass로 확보했습니다. dtype을 유지해
  scalar ISO로 변환하고, Polars native formatter/parse/equality가 lossless임을 확인합니다.
  Coarse 형식/실제 숫자 epoch/NaT와 dtype 없는 2-D array protocol은 유지합니다.
- 새 temporal58개가 scalar/0D/column/object/record/row/2D/structured·UTC/offset/DST·
  process TZ/C locale·비손실 formatter 거부·미지원 numeric date axis를 확인했습니다.
  모호한 mapping2D datetime column은 오류로 처리하고 실제 2D row 입력은 지원합니다.
  Arrow ns는 upstream safe conversion을 따르며 pandas 부재 등은 명시적으로 실패할 수
  있습니다. 모든 과거 timezone/precision/OS를 인증한 것이 아니며 DATA-05는 이 범위에서 **PASS**입니다.
- **FIND-014 (CI fixture 환경):** 359277c의 CI run39045121490은 Python3.10/3.12 jobs가
  성공했지만 Linux Rust smoke가 advanced regression action400에서 실패했고 Windows는
  취소됐습니다. Linux MSRV/lint/native unit은 성공했으나 전체 workflow는 failure입니다.
  Job117432201128 로그(ANSI 제거)·render-only 재현의 optional regression ImportError·
  설치 목록을 대조해 CI가 render만 설치한 불일치를 확인했습니다. Smoke job만 extra all로
  고치고 수정 전 실패하는 static guard를 추가했습니다. Runtime 필수 의존성은 유지합니다.
- Optional PyArrow26/Polars2를 포함해 **173개 모두 통과**, 프로젝트 대상은 **1045통과/
  27skip**, 최소 대상 **283통과/선택25skip/2142deselected/경고481**입니다. 격리된 all
  환경의 실제 Rust smoke와 Ruff211파일/format·Pyright·LSP5경로·계약·clean sdist→wheel을
  포함한9기록 명령이 exit0입니다. Browser/native unit 새 count나 수정 후 원격 CI 성공으로
  세지 않습니다. 개발 중 dtype 없는 fake-array 회귀도 별도 test로 잡아 수정 후 확인했습니다.
- 원문 체크리스트·프로젝트/lock·package/editor/spec 버전·tag/배포는 유지합니다.
  날짜는 ISO 저장이며 새로운 continuous date-axis 구현을 뜻하지 않습니다.

## 11차 — 실제 body 경계·framing·서버 PID 메모리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-body-boundaries-3c7c1_st`,
  [경로 제거 body/메모리/실행 요약](review_evidence/body_boundary_verification.json)도 보존합니다.
- 순차 probe **39개 통과**(Python13/Rust26). 실제 form·nested JSON form·JSON
  endpoint의 N-1/N 본문을 전송했고, 알려진 N+1 선언은 업로드 전에 거부했습니다.
  Rust unknown-length chunked는 N-1/N/N+1 및 `/undo`·`/reset` 초과에서 상태/PNG
  보존을 확인했습니다. Python은 미지원 Transfer-Encoding을 읽기 전 거부합니다.
- **FIND-011 (Python framing):** Transfer-Encoding 무시·중복 Content-Length 사용·짧은
  body를 그대로 반환하는 경계에서 수정 전6fail/4pass를 확보했습니다. `_read_body`가
  지원하지 않는 framing/중복 길이를 거부하고 실제 읽은 길이가 다르면 action 전에 실패합니다.
  실제 HTTP의 reset/잘린 action prefix3사례도 상태/history/PNG를 보존했습니다.
- **FIND-012 (Rust 전역 body 경계):** 본문을 추출하지 않는 `/undo`가 unknown-size
  chunked의 한도 확인 전에 상태를 바꿨습니다. 계획16MiB+1 중393216byte를 client가
  넘긴 뒤 연결이 중단됐으므로 전체 초과 body 수용/무제한 할당으로 과장하지 않습니다.
  기존 Axum limited Bytes extractor를 모든 handler 앞에 적용하고 request parts를
  보존해 넘깁니다. 새 parser/의존성은 없고 기존 DefaultBodyLimit도 유지합니다.
- Windows venv launcher와 실제 Python server PID가 달라 최초5MiB launcher 수치는
  폐기했습니다. 현재 Python worker의 `os.getpid`를 확인해 측정했고, 소유한 process tree
  종료와 listener 폐쇄도 확인했습니다. 기록된 server PID 수명 peak는 Python252.14MiB/
  Rust30.40MiB였습니다. 시작 후 수명 peak이지 request별 reset 값/전체 앱 hard limit이
  아니며 native 렌더 자식은 제외합니다. 동시 부하/렌더 CPU/모든 OS 보장은 아닙니다.
- 본문/fault unit13개와 지원 content-type/전송 경계 및 위 메모리 관찰을 근거로 SEC-03을
  **PASS** 처리합니다. 계산량/RSS hard cap인 SEC-04/PERF와 원격 OS gate는 그대로 남습니다.
- 최종 대상 **993통과/20skip**, Python 브라우저 **31통과**, native Rust **15통과/
  helper1ignored**, 실제 Rust HTTP/browser도 통과했습니다. 최소 대상은 **232통과/
  선택18skip/2142deselected/경고481**이며 전체 matrix/zero-warning 주장은 아닙니다.
  Ruff209파일/format·Pyright·LSP7경로·Clippy/fmt·계약·clean sdist→wheel까지13기록
  명령이 exit0입니다. MSRV/Linux 실행 결과로 세지 않습니다.
- 새 순차 probe를 Windows/Linux Rust CI에 구성했지만 원격 실행은 관찰하지 않았습니다.
  원문 체크리스트·core 의존성/lock·package/editor/spec version·tag/배포는 유지합니다.

## 10차 — 실제 optional table·SQL cursor 소유권

- 실제 PyArrow26.0.0/Polars2.0.0을 별도 venv에서 실행했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-libs-_bgvxl_h`,
  [경로 제거 형식/SQL 실행 요약](review_evidence/table_sql_verification.json)도 보존합니다.
- 격리 환경의 **114개 전부 통과/skip0**, 추가한 CI 명령도 로컬 **114통과**입니다.
  두 결과는 같은 범위의 별도 실행이므로228개 고유 검사로 합산하지 않습니다.
  Mapping/records/rows/NumPy2D/structured/pandas/SQL query/cursor/generic to_dict/
  Arrow·chunks·dictionary/Polars·categorical14경로에서 값/결측/그룹/행 순서와
  원본 비변경·line/scatter/lineplot의 사용 관측을 비교했습니다. DATA-01은 **PASS**입니다.
- 실제 테이블의 signed64 범위에서2^53초과 정수·boolean·Unicode·null·UTC microsecond,
  empty named columns와 중복 Arrow 이름을 확인했습니다. Decimal/무한대는 유효 JSON으로
  coercion하지 않습니다. 모든 optional 버전/정밀도/timezone/OS를 인증한 결과는 아닙니다.
- **FIND-010 (DATA-07 resource):** connection+query의 내부 생성 cursor를 success/
  execute/fetch/shape/duplicate 실패 뒤 명시적으로 닫지 않음을 수정 전5fail/2pass로
  확보했습니다. `to_columns`의 해당 경로만 finally로 close(지원 시)하고 caller-owned
  executed cursor/connection은 보존합니다. Query/params를 그대로 넘기며 commit/rollback
  하지 않고 close 실패/예외 context도 전파합니다. 새 SQL 회귀10개 통과, DATA-07은 **PASS**입니다.
- 프로젝트 기본 환경은 **980통과/20skip**, 최소 data 대상은 **95통과/18skip/
  2266deselected/경고13**입니다. 기본20skip은 선택 라이브러리18·Windows조건2이며
  선택 검사 추가로 skip 수가 늘어난 것이지, 실제114-pass 검증을 생략한 것이 아닙니다.
  최소 환경에는 최신 optional 라이브러리를 설치하지 않아 그 버전 floor를 주장하지 않습니다.
- Ruff207파일/format·Pyright·LSP6경로·계약 sync·clean sdist→wheel을 포함해9기록
  명령이 exit0입니다. 새 CI step은 optional 라이브러리를 upfront import한 뒤 실행하도록
  구성했지만 원격 CI 성공으로 세지 않습니다. 이번 browser/Rust native 새 실행도 없습니다.
- 설치했던 전용 venv는 결과·버전·지문을 남긴 후 제거했습니다. 원래 프로젝트에서는
  pyarrow/polars import가 계속 불가함과 pyproject/uv.lock 비변경을 확인했습니다.
  로그/receipt만 보존하며 원문 체크리스트·버전/tag/배포는 유지합니다.

## 9차 — 모든 모델 필드 codec·Python 실행 경로

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-codec-paths-2t3d4dl_`;
  [경로 제거 실행/child argv/codec 요약](review_evidence/codec_path_verification.json)도 보존합니다.
  기반96a8592와 기존 로컬 변경은 유지했으며 이번에는 새 제품 결함/수정이 재현되지 않았습니다.
- 전체 dataclass 탐색으로 **24모델/272필드**의 nondefault·대체 union·null/Unicode/
  big integer fixture3개를 생성했습니다. Schema-valid지만 호환되지 않는 옵션을 함께 채운
  **직렬화 전용 fixture**이며 렌더 가능성/모든 옵션 조합 동등성을 뜻하지 않습니다.
- `test_review_full_spec_fields.py` **69개**가 필드 누락/기본값으로 가려진 손실·JSON
  기본 타입·배열 순서·nested model 복원을 검사합니다. 등록37예제의 정상 spec/JSON
  왕복도 별도로 확인했습니다. Raw NumPy float64→JSON builtin float는 허용된 정규화로
  값 동등성을 확인하며, 초기5개 dtype-identity 실패를 제품 버그로 세지 않았습니다.
- 실제 Python 생성 JSON→Rust strict FigureSpec→JSON 파일→Python 모델 복원을 실행해
  fixture3개 전체를 비교했습니다. Field introspection/checked-in snapshot으로 새 필드가
  조용히 미검증 상태가 되지 않게 하며 버전은 기존0.1을 유지합니다. JSON-01은 **PASS**입니다.
- Interpreter probe는 별도 한글/공백/`&` venv·임시 경로에서 PATH default/env/flag
  세 경우 각4개의 실제 capabilities/apply/render child를 확인했습니다. `sys.executable`,
  prefix/version/원본 argv와 PNG를 검증하고, 잘못된 명시 flag는 env의 정상 Python으로
  fallback하지 않았습니다. Startup recorder는 그 임시 venv 안에만 exclusive 생성합니다.
- 첫 offline setup은 캐시 부족으로 중단되어 성공/제품 결함으로 세지 않았습니다. 명시한
  준비 변경 후 같은 NumPy/Matplotlib 버전을 임시 venv에만 내려받고 정리했습니다.
  프로젝트 패키지/의존성/lock은 바꾸지 않았습니다. 실제 Windows만 실행했으며 추가한
  Windows/Linux CI matrix는 아직 실행을 관찰하지 않아 RUST-02는 **RUNNING**입니다.
- 기록된 대상 **968통과/4skip**, native Rust **lib14+main1통과/helper1ignored**,
  최소 환경 **207통과/2skip/2142deselected/경고481**. Clippy/fmt·Ruff205파일/format·
  Pyright·LSP6경로·계약 sync·clean sdist→wheel도 통과했습니다. 이 phase의 browser
  새 실행은 없고 이전31개는 그대로 과거 결과입니다. MSRV/Linux 전체 실행도 아닙니다.
- 12개 기본 명령 뒤 QA startup-hook의 target/exclusive-create 검증을 보강하고 그
  스크립트·Ruff/format/Pyright/packaging을 별도로5명령 재실행했습니다. 변경 없는 core/
  codec 대상968개를 새 QA 변경까지 검증한 것으로 확대하지 않으며 source revision과
  17개 성공 receipt를 구분합니다. 원문 체크리스트·배포/version/tag는 유지합니다.

## 8차 — 공통 상태 경로·실패 격리·HTTP 경계

- 기반96a8592 위의 로컬 변경(6/7차 포함)을 확인했습니다. 최종 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-editor-boundary-final-hdtdgy50`,
  [경로 제거 실행/상태 해시/argv 요약](review_evidence/editor_boundary_verification.json)도 보존합니다.
- 최종 대상 **899 통과, 4 skip**, Python 실제 브라우저 **31 통과**. 최소 환경 대상은
  **138 통과, 2 skip, 2142 deselected, 경고481**입니다. Skip은 기존 선택 의존성/
  Windows 조건이며, 경고는 별도10-case 가시화 조사에서 Matplotlib3.8/pyparsing
  deprecation/diagnostic을 확인했습니다. zero-warning 또는 전체 경고 조사를 주장하지 않습니다.
- Rust native **lib13+main1 통과/보조 helper1 ignored**, 실제 HTTP/browser의 상태·
  실패·Host/Origin·CSP·선언 크기 검사 통과. Native IPv6 `::1` listener도 실제 실행해
  HTTP/Host/header를 확인했습니다. Clippy/fmt·Ruff203파일/format·Pyright·LSP7경로·
  계약 sync·clean sdist→wheel까지13개 기록 명령이 최종 exit0입니다. MSRV1.88 결과는 아닙니다.

| ID | 판정 | 실행한 근거 |
|---|---|---|
| STATE-03 | PASS | 공통 fixture10작업의 fluent/functional/Store/CLI/Python session·HTTP/Rust agent·지원 form에서 중간/최종 FigureSpec 비교 |
| EDIT-01 | PASS | Python _build_action 및 실제 양 editor 폼/agent의 theme·size·title·layer metadata 비교; 없는 Rust UI는 agent로 수행했다고 구분 |
| RUST-01 | PASS | PythonBridge apply/render argv와 CLI source를 대조; preview만 --preview, vector는 원본 export; 실제 공통 상태 JSON 비교 |
| HIST-03 | PASS | validation/손상 JSON/실제 Matplotlib render 실패에서 양 editor spec/history/PNG/redo 보존과 후속 정상 요청 확인 |
| SEC-01 | PASS | IPv4/IPv6 bind guard와 실제 loopback listener·localhost/IPv4/IPv6 Host matrix, malformed/forwarded Host 거부 |
| SEC-02 | PASS | scheme/host/port/null/cross-site 거부·Origin 없는 CLI 및 same-origin 정상 payload 허용; 브라우저 null-Origin payload 거부 |
| SEC-05 | PASS | 정상/error/static/PNG/PDF/SVG·403/404/413 application header와 실제 htmx swap의 console/CSP event 확인 |
| SEC-03 | RUNNING | 선언16MiB+1을 업로드 전 거부하는 경계만 확인; 실제 한도 전후·content type·chunked·peak RSS matrix는 남음 |

### 재현한 보완점과 실패 실행의 처리

- **FIND-008 (application 응답 계약):** Rust의 기존 Host/Origin 거부는 차단 자체는
  성공했지만 공통 no-store/CSP header 처리를 우회했습니다. 실제 smoke의403 header
  assert 실패를 먼저 확보한 뒤 거부도 같은 header 경로로 보냈습니다. 접근 조건은 그대로입니다.
- **FIND-009 (선행 경계 보강):** 선언 Content-Length16MiB+1만 보냈을 때 body를
  기다려5초 timeout이 났습니다. middleware가 이를413으로 먼저 거부하고 기존 streaming
  DefaultBodyLimit은 유지합니다. 무제한 payload 수용이 확인된 것도, SEC-03 전체가 끝난 것도 아닙니다.
- 처음 묶음 `mudplot-review-editor-boundary-mu7xq2yn`은 Rust Origin 거부의 Windows
  WinError10053 및 로그 reader의 UTF-8 decode 오류로 중단했습니다. 뒤 검사는 실행하지
  않았고 성공으로 세지 않았습니다. 원본 실패 로그는 그대로 보존했습니다.
- 현재 거부 matrix는 body decode/upload 이전에403이어야 하는 **header-only** 요청으로
  분리하고, 정상 same-origin/agent 및 브라우저 null-Origin은 실제 payload로 확인합니다.
  Windows 연결 중단의 원인/일반 네트워크 신뢰성이 해결됐다고 주장하지 않습니다. 최종
  재실행은 명시한 UTF-8 로그 환경을 사용했으며 테스트 안의 retry/fallback은 추가하지 않았습니다.

공통 fixture는 `tests/fixtures/review_state_paths.json`과 `review_http_boundaries.json`에
있고 sdist 포함도 검사합니다. 최종 상태 canonical hash는 native form/agent 모두
`926e9f349bcb681d626b8c9e1a2215fcd39932d5a923bf48ed3975a47fc9f6c9`였습니다.
이 통과를 전체 UI 동등성/보안 인증/전체 suite/OS/릴리스 gate로 확대하지 않습니다.

## 7차 — 결측 좌표·중첩 상태·이력 경계

- 현재 기반96a8592 위의 로컬 변경(6차 포함)을 검사했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-missing-history-btis6dds`, 저장소 내
  [경로 제거 검증/커서 해시 표](review_evidence/missing_state_verification.json)도 보존합니다.
- 대상 **859 통과, 4 skip**: 실제 PyArrow/polars 부재2·Windows 조건2입니다. 최소
  Python3.10/NumPy1.23 대상 **98 통과, 선택 의존성2 skip, 2142 deselected, 경고13**.
  실제 Rust HTTP/browser의 단계별 spec/PNG·branch·JSON corpus가 통과했습니다.
  Ruff201파일/format·Pyright·LSP5경로 확인·계약 sync·clean sdist→wheel도 exit0입니다.
  Native Rust unit/MSRV 전체를 이번에 다시 실행한 결과로 보고하지 않습니다.
- **FIND-007 (DATA-03 production):** 범주/ISO 날짜 문자열 x의 null이 문자열 `None`
  범주가 되며 결측 관측을 정상 점처럼 표시했습니다. 수정 전10개 실패를 확보했습니다.
  `_x_values`가 non-null 범주만 등록하고 원래 행 위치에는 NaN을 남기도록 수정했습니다.
  Raw line은 단절, scatter는 mask하며 실제 문자열 `"None"`·shared/y2 정렬·JSON 원행은
  유지합니다. 새 날짜 축/통계 정규화 정책은 추가하지 않았습니다.

| ID | 판정 | 실제 확인한 경계 |
|---|---|---|
| STATE-01 | PASS | 중첩 data/matrix/theme/reference의 성공·실패 입력 비변경, 반환값과 AddLayer action 분리 |
| STATE-02 | PASS | Plot.spec/Store.state/dispatch/history·listener별 중첩 mutation 격리 및 replay 유지 |
| HIST-01 | PASS | Store와 시작 직후 Rust session의 끝까지 undo/redo·빈 경계; 단계별 spec/PNG·커서 해시 비교 |
| HIST-02 | PASS | Python/Rust A→B→C→undo→D 뒤 C redo 불가, history/저장 spec/PNG는 D branch 유지 |
| DATA-03 | PASS | None/NaN/nullable/NaT의 정규화와 raw line 단절·scatter mask·lineplot 사용 표본을 분리 검증 |
| DATA-01 | RUNNING | mapping/records/rows/NumPy2D/structured/pandas/SQL의 값·순서·그룹·원본 비변경은 확인했으나 실제 PyArrow/polars는 미실행 |
| HIST-04 | RUNNING | Python open/reset fresh와 Rust undoable snapshot 차이를 확인·문서화; 전체 dirty/저장 대상/reset 조합 검토는 남음 |

이력 코드의 제품 수정은 없었습니다. 첫 Rust probe는 open을 이력 초기화로 잘못 가정해
실패했습니다. 구현을 읽어 기존 정책을 확인한 뒤 빈 경계 검사를 서버 시작 직후로 옮기고
Rust open의 undo/redo를 따로 확인했습니다. 잘못된 probe를 제품 결함으로 세지 않았으며
재현한 결측 좌표 문제와 구분해 기록합니다. 모든 항목/OS/접근성/보안/릴리스 완료는 아닙니다.

## 6차 — DATA-02 입력 구조 검증 마무리

- 기반 commit은 `96a85922293fac14f5aa5e3dcb45b7c9ec66ff1f`이며 그 위의 로컬 변경을
  검사했습니다. 원문 기준 SHA와 현재 검토 기반을 혼동하지 않습니다. 버전/릴리스는 유지합니다.
- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-shapes-f2y9mmx2`.
  [경로 제거 검증 요약](review_evidence/data_shape_verification.json)에 명령/환경/
  소스·원문 지문/원본 log hash와 결과를 별도 보존합니다.
- 실제 결과: **677 통과, Windows 조건 2 skip**, 최소 Python3.10/NumPy1.23 adapter
  **66 통과, 2142 deselected, 경고13**. Ruff200파일/format·Pyright·계약 sync·clean
  sdist→wheel도 exit0입니다. 이 대상 결과를 전체 suite/MSRV/Linux로 확대하지 않습니다.
- **FIND-006 (DATA-02 production):** 혼합 입력의 record가 mapping이 아니면 위치 없는
  AttributeError가 났고 positional/DB 행의 문자열/bytes/dict는 문자/key 열로 조용히
  바뀌었습니다. 수정 전19fail/9pass를 확보했습니다. `_records_to_columns`가 record
  타입/중복 key의 index를 검사하고 `_row_values`가 두 row 경로에서 잘못된 타입을
  pivot 전에 거부합니다. 유효한 row와 sqlite3.Row·record 누락-key/null 동작은 유지합니다.

| 검증 범위 | 실제 테스트·결과 |
|---|---|
| 잘못된 record/positional/DB row·너비 | test_review_data_contracts.py의 index/expected/타입 검사, 입력 비변경 확인 |
| 열 길이 불일치 | mapping/DataFrame·Arrow·to_dict duck protocol에서 값 그대로 보존 후 validate/assert_valid가 이름별 길이로 거부 |
| 없는 x/y/group | line/scatter에서 panel/layer/column 위치 오류와 validation 입력 비변경 확인 |
| 중복 열/충돌 | 실제 pandas duplicate/string-conversion collision과 기존 mapping/record/DataFrame/Arrow/DB 중복 거부 검사 |
| 실패 격리 | 잘못된 editor import/SetData 뒤 state/history/PNG/redo 보존; CLI apply의 입력·기존 출력 보존 |
| 정상 호환 | sparse-record 첫 등장 열 순서/null, 정상 positional/DB row, sqlite3.Row·caller connection 재사용 |

DATA-02를 **PASS**로 닫습니다. 직접 실행한 새/기존 DATA-02 회귀 파일은49개이고
최소 환경에서도 전부 실행했습니다. 실제 PyArrow/polars는 설치하지 않았으며 그 라이브러리
전체 호환성이나 DATA-01의 형식 간 동등성을 완료한 것으로 세지 않습니다. Arrow 등은
이 항목의 malformed-input duck protocol만 확인했습니다. 새 성능/결측/정렬 정책은 없습니다.

## 5차 — 같은 corpus로 Python/Rust JSON 경계 대조

- 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-cross-json-65s92n46`.
  대상 **597 통과, Windows 조건 2 skip**; Rust all-targets **lib13+main1 통과,
  의도한 helper1 ignored**; 실제 HTTP/browser smoke, Clippy -D warnings/fmt,
  Ruff200파일/format/Pyright/schema sync/clean sdist→wheel 검사 exit0입니다.
  현재 compiler1.99이지 MSRV1.88 검증은 아닙니다. 환경/체크리스트·소스 SHA/
  명령·exit/JUnit/log와 실제 수정 전 실패 요약을 보관했습니다.
- 공유 fixture `tests/fixtures/review_json_boundaries.json`: 잘못된 spec19개,
  action11개, 정상 spec2개. API3경로/CLI4경로/Python editor/HTTP와 Rust JSON/raw
  action/open에서 거부·기존 state/history/preview/output 보존을 대조합니다.
- fixture 자체에도 검사를 넣었습니다. version 오류가 아닌 음성 입력에는 정상
  version을 명시하고, 두 정상 입력의 suptitle을 다르게 하여 stale state가 성공으로
  보이지 않게 했습니다. 이전 약한 corpus probe 결과는 완료 증거로 쓰지 않습니다.

| ID | 상태 | 실제 확인한 경계 |
|---|---|---|
| JSON-02 | PASS | NaN/±Infinity/±1e400 raw 입력과 strict 저장 거부; mapping/records/rows/NumPy/nullable pandas 각각 missing→null/±Infinity를15경우로 구분 |
| JSON-06 | PASS | root/column/array object 예약 key, escaped key, lone high/low/key surrogate, 비문자열 key 거부; 정상 한글/기호/emoji·valid pair·일반 문자열 reserved spelling 유지 |
| JSON-07 | PASS | explicit0.1과 version 생략의 동일 기본값; unknown future/unimplemented old/빈 문자열/숫자/bool/null/array 거부, CLI·editor 실패 시 기존 상태 보존 |

### 실제 재현 후 수정한 Rust 차이

- **FIND-004 (JSON-06 production):** serde arbitrary_precision은 실제 사용자 object
  `{"$serde_json::private::Number":"1"}`를 숫자로 바꿀 수 있었습니다. 기존 visitor는
  내부 number-map과 실제 key를 구별하지 못했습니다. unit exit101과 정상 version의
  nested HTTP open에서 spec 변경을 먼저 재현했습니다. 공통 from_json_strict에 원본
  string token 검사를 추가했습니다. serde string deserializer로 escape를 해석하고
  뒤따르는 colon으로 실제 property key만 검사하므로 큰 정수와 일반 문자열은 유지합니다.
  새 별도 JSON parser/의존성/숫자 강제 float 변환은 넣지 않았습니다.
- **FIND-005 (JSON-07 production):** Python은 version 생략을 현재 기본값으로 읽지만
  Rust envelope는 missing field version으로 거부했습니다(unit exit101/HTTP mismatch).
  Rust의 serde default를 내장 default_spec.json의 version에 연결했습니다. 별도 version
  literal이나 null/unknown 허용은 추가하지 않았습니다. 서로 다른 정상 state를 사용해
  실제 commit을 확인했으며 기존 state와 같은 값으로 거부가 가려지지 않게 했습니다.

원문 체크리스트/공개 version/tag/deploy는 유지합니다. 이 범위의 PASS를 모든 필드/
OS/성능/지원 MSRV/릴리스 gate로 확대하지 않습니다. DATA-02와 나머지 P0는 진행 중입니다.

## 4차 — JSON 경계·어댑터 데이터 손실 방지

- 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-json-ijbqg6n6`.
  현재 로컬 작업 트리/Agg의 **404 통과, Windows 조건 2 skip**, 최소 Python3.10/
  NumPy1.23 adapter **25 통과, 2142 deselected, 경고13**입니다. Ruff199파일/format/
  Pyright/schema sync도 exit0이며 manifest/JUnit/명령/환경 override/log를 보관했습니다.
- **FIND-003 (DATA-02 P0 production):** positional ragged row의 추가 값이 조용히
  잘리거나 짧은 행이 IndexError를 냈고, DB cursor description과 row 길이 불일치도
  zip에서 조용히 잘렸습니다. 수정 전 7 fail/1 pass를 확보했습니다. data.py의
  `_rows_to_columns`/`_cursor_to_columns`에서 pivot 전에 너비를 검사하고 row index/
  실제 수/expected 수가 있는 ValueError를 반환합니다. 정상 값/순서/빈 열 입력은 유지합니다.
- 새 `test_review_data_contracts.py`8개와 기존 adapter 검사를 실행했습니다. DATA-02는
  전체 형식·필수 열/중복 열 매핑을 모두 닫기 전이므로 RUNNING입니다.
- JSON-05는 **PASS**입니다. 10^1000을 x/y/matrix/style/size에 넣어 구조 보존과
  PNG/PDF/SVG CLI 실패를 분리한15개, editor 실패 후 state/history/preview 보존과
  재사용1개를 확인했습니다. 임의 정밀도 plotting 지원으로 바꾸지 않습니다.
- JSON-02 raw NaN/±Infinity/±1e400의 CLI4경로20개와 mapping/record/row/NumPy/
  nullable pandas 결측→null5개를 보강했습니다. Infinity는 유효값으로 coercion하지
  않고 strict JSON 저장에서 거부합니다. 전체 언어/진입점 표가 남아 RUNNING입니다.
- 한 초기 회귀 실행은 MPLBACKEND 미설정으로 Tk/Tcl 환경 오류2개가 났습니다.
  이를 제품 결함이나 통과로 세지 않았고 Agg로 재실행59개 통과 후 기록한 본 검증을
  수행했습니다. Native GUI/Tk 지원을 이번에 고친 것은 아닙니다.

## 후속 JSON·출력 검증 — 2/3차

- 2차 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-json-output-mx5owq8x`.
  Python **338 통과, Windows 조건 2 skip**, Rust lib **11 통과/보조 helper 1 ignored**,
  실제 Rust HTTP/browser smoke·schema sync·Ruff·Pyright·Rust fmt exit0입니다.
- 3차 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-windows-output-gdp35khy`.
  JSON/출력/에디터 대상 **354 통과, Windows 조건 2 skip**, Ruff/format/Pyright/
  schema sync/clean sdist→wheel 검사 exit0입니다. 명령/로그/JUnit/환경과 source
  hash는 각 `environment.json`, `receipts.json`, `contracts.xml`에 있습니다.
- 범위: 현재 로컬 작업 트리, Windows/Python3.12.15. Rust는 설치 compiler1.99.0이며
  MSRV1.88 실행으로 간주하지 않습니다. 원문 SHA256은 각 manifest와 일치합니다.

| ID | 판정/기대 결과 | 실제 증거 |
|---|---|---|
| JSON-03 | PASS: root/nested/array object의 같은/다른 duplicate key 거부, 기존 state/preview/output 유지 | test_review_json_contracts.py의 API/CLI 42+6 cases; Python HTTP open/raw-action; Rust strict unit+JSON/raw/open HTTP smoke |
| JSON-04 | PASS: 2^53/signed·unsigned64/큰 양·음 integer 구조 보존; 정밀 렌더 보장은 아님 | Python known data field boundary; model.rs signed-boundary unit; 실제 bridge open/spec/action 왕복 unused_integer_boundaries |
| OUT-03 | PASS: JSON/PNG/PDF/SVG partial-write/flush-close/fsync/replace 실패 시 기존 bytes와 staging/Figure 정리 | test_review_output_contracts.py::test_out_03_atomic_failure_retains_previous_bytes_and_cleans_staging 16 cases, 공개 save API에서 fault injection |

OUT-04는 RUNNING입니다. 실제 Win32 delete-sharing lock, 읽기 전용 대상, 없는 상위
경로·디렉터리 대상까지 확인했으나 디스크 공간·전체 권한·다른 OS를 완료 처리하지
않습니다. JSON-06/07도 추가 Python/Rust 사례는 통과했지만 전체 필드/진입점 표를
완료하지 않아 RUNNING을 유지합니다. 전체 gate 승인이나 미측정 성능 주장은 없습니다.

### 재현한 문제와 최소 수정

- **FIND-001 (연결 검사):** Rust generated capability 테스트가 registry를36으로 고정해
  실제37에서 exit101. model.rs 기대 수를37로 갱신하고 clustermap의 matrix 필수 필드와
  cluster/heatmap/colorbar 지원을 별도 assert했습니다. 실패 요약과 수정 후 lib 로그는
  2차 증거에 있습니다. 제품 전체 JSON 손상으로 과장하지 않습니다.
- **FIND-002 (OUT-04 production):** Windows 읽기 전용 대상의 mode를 staging에 복사하여
  replace 실패 뒤 read-only .tmp 삭제가 실패함을 네 형식에서 재현했습니다(pytest-508,
  수정 전 4 fail). io.py::_atomic_destination에서 POSIX mode 복사만 non-Windows로
  제한했습니다. 원본 읽기 전용 속성/bytes를 바꾸거나 임의 파일을 chmod하지 않습니다.
  실제 잠금4·읽기전용4·잘못된 경로8과 원자성16 검사 통과. POSIX mode/symlink 두 사례는
  Windows에서 skip이므로 다른 OS 검증 완료로 보고하지 않습니다.

## 1차 확인된 계약과 새 회귀 검사

| ID | 판정/기대 결과 | 구현 심볼 | 실제 증거 |
|---|---|---|---|
| BASE-01 | PASS: HEAD/tag/dirty 범위와 파일 지문 확보 | git working tree | environment.json / git-status.txt / tracked-diff.patch |
| STATE-04 | PASS: mp.apply 실패는 입력 state/actions 보존, 부분 반환 없음 | mudplot/api.py::apply; reducer.py::reduce_all | test_review_state_contracts.py::test_state_04_* (2개) / contracts.xml |
| STATE-05 | PASS: Plot.apply/Store.dispatch_all은 완료 prefix 유지, 후속 사용/redo 의미 유지 | Plot.apply; Store.dispatch_all | test_review_state_contracts.py::test_state_05_* (2개) / contracts.xml |
| STATE-06 | PASS: listener 예외 전파하되 이미 commit된 state/history 유지 | Store._dispatch; subscribe | test_review_state_contracts.py::test_state_06_listener_failure_occurs_after_commit_and_is_not_rollback / contracts.xml |

1차 당시 OUT-03/04는 RUNNING이었습니다. 당시12개 검사는 partial-write/fsync/replace만 다뤘으며 위 후속 증거로 확대했습니다. 과거 결과를 나중 범위의 통과로 소급하지 않습니다.

새 코드: tests/test_review_state_contracts.py(5), tests/test_review_output_contracts.py(12). 기존 테스트가 다루지 않던 실패 단계/형식만 추가했고 production semantics는 변경하지 않았습니다.

## 전체 ID 추적

**아래 구현/테스트는 검토 후보입니다. 해당 파일 존재/수집/이전 통과만으로 PASS가 아닙니다.** 후보가 넓은 항목은 ID별 심볼/fixture/실행 결과를 좁혀야 합니다.

| ID | 우선순위 | 상태 | 확인 항목 | 구현 후보 | 테스트/증거 후보 |
|---|---|---|---|---|---|
| BASE-01 | P0 | PASS | 커밋·태그·작업 트리의 기준선 기록 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-02 | P0 | PASS | 지원 범위와 비목표 확인 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-03 | P0 | PASS | 검증 환경 명세 수집 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-04 | P0 | PASS | 변경 전 테스트 기준선 확보 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-05 | P1 | RUNNING | 기존 테스트와 체크리스트 매핑 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-06 | P1 | PASS | fixture와 증거 데이터 분리 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-07 | P1 | PASS | 문서 계약 충돌 처리 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| STATE-01 | P0 | PASS | reducer의 입력 비변경 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-02 | P0 | PASS | 공개 스냅샷의 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-03 | P0 | PASS | 상태 변경 경로의 일관성 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-04 | P0 | PASS | mp.apply의 실패 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-05 | P0 | PASS | 비트랜잭션 배치 API의 계약 보존 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-06 | P0 | PASS | listener 예외의 commit 시점 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-07 | P1 | PASS | 결정성과 암묵적 전역 상태 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-08 | P1 | PASS | 잘못된 참조와 경계 인덱스 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-09 | P1 | PASS | 검증과 부수효과 경계 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| HIST-01 | P0 | PASS | 기본 undo/redo와 경계 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-02 | P0 | PASS | undo 이후 분기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-03 | P0 | PASS | 편집기 action/import/render 실패 원자성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-04 | P1 | PASS | reset과 open의 이력 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-05 | P1 | PASS | no-op action의 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-06 | P1 | PASS | 긴 이력의 재생 정확성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-07 | P2 | PASS | 연속 드래그 action 합치기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-08 | P2 | PASS | 체크포인트와 이력 제한 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| JSON-01 | P0 | PASS | 공식 지원 필드의 손실 없는 왕복 | io.py/spec.py; model.rs::full_field_fixture_preserves_types_values_and_array_order | test_review_full_spec_fields.py(69); Python→Rust→Python 9차 artifact |
| JSON-02 | P0 | PASS | 비유한 숫자의 경계 분리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-03 | P0 | PASS | 재귀 중복 키 거부 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-04 | P0 | PASS | 큰 정수의 구조적 보존 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-05 | P0 | PASS | float 범위 밖 좌표의 실패 처리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-06 | P0 | PASS | 예약 키·문자열 키·Unicode 유효성 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-07 | P0 | PASS | 알 수 없는 spec 버전 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-08 | P1 | PASS | 알 수 없는 필드의 명시된 처리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-09 | P1 | RUNNING | 생략·null·자동값·기본값 구분 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-10 | P1 | PASS | canonical serialization과 해시 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-11 | P1 | PASS | 스키마·capabilities·문서 동기화 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-12 | P1 | PASS | JSON 크기·깊이·손상 입력 복구 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| DATA-01 | P0 | PASS | 입력 형식 간 동일 데이터의 동등성 | data.py::to_columns/_to_list/_mapping_to_columns | test_review_missing_data.py(14formats); test_review_table_formats.py(13); 실제 optional114-pass 실행 |
| DATA-02 | P0 | PASS | 열 길이·필수 열·중복 열 | data.py::_records_to_columns/_row_values; validate.py::_check_data_integrity/_check_column | test_review_data_contracts.py(49); test_data.py; test_validate_hardening.py; 6차 증거 |
| DATA-03 | P0 | PASS | 결측값의 정규화와 렌더링 분리 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-04 | P1 | PASS | 혼합 그룹 식별자 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-05 | P1 | PASS | 날짜·시간·timezone | data.py::_plain_value/_to_list/2D datetime path | test_review_temporal_precision.py(58); 실제 optional/일반/minimum 12차 기록 |
| DATA-06 | P1 | PASS | NumPy scalar와 지원하지 않는 객체 | data.py::_plain_value missing/item guards | test_review_scalar_boundaries.py(71); optional/project/minimum 13차 기록 |
| DATA-07 | P1 | PASS | SQL 파라미터와 연결 소유권 | data.py::to_columns query finally | test_review_sql_ownership.py(10); named/tuple params·transaction·borrowed cursor·cleanup failures |
| DATA-08 | P1 | PASS | 빈 데이터·상수·단일 관측값 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-09 | P1 | PASS | 행 순서·정렬·중복 x의 정책 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| PLOT-01 | P0 | PASS | 전체 등록 레이어의 실행·계약 커버리지 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-02 | P0 | PASS | 범주형 x의 레이어 간 정렬 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-03 | P0 | PASS | 그룹·패널 간 스타일 일관성 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-04 | P0 | PASS | 보조 y축 소속과 스케일 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-05 | P1 | PASS | shared axes와 독립 설정 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-06 | P0 | PASS | heatmap·surface 행렬 방향 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-07 | P1 | PASS | quiver·3D·polar의 좌표 의미 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-08 | P1 | PASS | 연속 색상과 colorbar 의미 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-09 | P1 | PASS | bar·stack·band·errorbar 정렬 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-10 | P1 | PASS | log scale과 유효 영역 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-11 | P1 | PASS | annotation·legend의 좌표계 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-12 | P1 | PASS | 겹침·z-order·alpha와 클리핑 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| STAT-01 | P0 | PASS | regplot의 적합값 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-02 | P0 | PASS | confidence band의 의미 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-03 | P1 | PASS | 회귀의 퇴화 입력 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-04 | P1 | PASS | histogram bin·density·weights | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-05 | P1 | PASS | KDE bandwidth·적분·퇴화 입력 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-06 | P1 | PASS | box·violin의 집계 정의 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-07 | P1 | PASS | jitter와 난수 재현성 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-08 | P1 | PASS | 통계 전처리의 관측 대응 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| COLOR-01 | P0 | PASS | 색 공간 변환의 기준값 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-02 | P0 | PASS | CIEDE2000의 독립 reference | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-03 | P1 | PASS | gamut 처리 이후 품질 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-04 | P1 | PASS | CVD 시뮬레이션 조건 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-05 | P1 | PASS | preset 범주 수의 경계 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-06 | P1 | PASS | 균일 명도와 흑백 구분의 분리 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-07 | P1 | PASS | 중복 표현의 일관성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-08 | P1 | PASS | 팔레트 결정성·seed·tie-break | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-09 | P1 | PASS | 실제 그림 크기의 가독성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-10 | P2 | PASS | 품질 report와 대외 문구 정합성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| LAY-01 | P0 | PASS | 최종 파일의 물리 크기 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-02 | P0 | PASS | tight 옵션의 명시적 차이 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-03 | P1 | PASS | TeX preset·columns 적용 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-04 | P1 | PASS | 긴 제목·suptitle·범례 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-05 | P1 | PASS | 외부 범례·colorbar·멀티패널 조합 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-06 | P1 | PASS | 배치 불가능 상태의 처리 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-07 | P1 | PASS | 폰트 부재·fallback·한글 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-08 | P1 | PASS | 반복 렌더링의 스타일 격리 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-09 | P1 | RUNNING | DPI·벡터 출력과 UI 위치의 일치 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| OUT-01 | P0 | PASS | 동일 환경의 반복 출력 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-02 | P1 | PASS | volatile metadata·ID | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-03 | P0 | PASS | 단일 파일 저장의 원자성 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-04 | P1 | PASS | 출력 실패·잠금·권한 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-05 | P1 | PASS | Figure 소유권과 누수 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-06 | P1 | PASS | PGF bundle 한계 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-07 | P1 | PASS | 참조의 형식별 의미 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-08 | P1 | PASS | TeX 컴파일로 참조 확인 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-09 | P1 | PASS | SVG·TeX·HTML 문자열 경계 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-10 | P2 | PASS | 출력 provenance 기록 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| EDIT-01 | P0 | PASS | UI 입력과 공통 action | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-02 | P1 | PASS | 드래그·키보드 위치 편집 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-03 | P1 | PASS | htmx 교체 이후 상태·이벤트 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-04 | P1 | PASS | 지연 응답과 최신 preview | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-05 | P1 | PASS | 두 탭·동시 agent 요청 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-06 | P1 | PASS | open·export·실패 후 회복 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-07 | P1 | PASS | 입력 오류의 위치·설명 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-08 | P1 | PASS | 키보드 접근과 상태 피드백 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-09 | P1 | PASS | agent 응답의 기계 판독성 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| RUST-01 | P0 | PASS | Python CLI 위임의 계약 일치 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-02 | P0 | PASS | Python 실행 파일 선택과 quoting | main.rs::parse_args; python.rs::PythonBridge | check_python_bridge_paths.py Windows/Linux CI jobs success for781f3f5; 14차 remote snapshot |
| RUST-03 | P1 | PASS | 실패한 subprocess와 출력 경계 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-04 | P1 | PASS | 120초 timeout과 자식 정리 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-05 | P1 | PASS | preview 2000px 제한과 원본 보존 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-06 | P1 | PASS | Rust history와 캐시의 commit 순서 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-07 | P1 | PASS | 공유 static 자산·버전 정합성 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| SEC-01 | P0 | PASS | loopback bind와 Host 검증 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-02 | P0 | PASS | Origin과 mutation 경계 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-03 | P0 | PASS | 16 MiB 요청 한도 | _Handler._read_body; protect_local_boundary limited Bytes | test_review_body_framing.py(13); check_request_body_limits.py(39); 실제 PID RSS/peak·상태 보존 11차 기록 |
| SEC-04 | P1 | RUNNING | 작은 요청의 과도한 계산 방어 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-05 | P1 | PASS | CSP·no-store·브라우저 header | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-06 | P1 | PASS | 파일 경로·임시 파일 경계 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-07 | P1 | PASS | 외부 참조·입력의 실행 금지 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-08 | P1 | PASS | 오류 로그·비밀값·의존성 위험 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| PERF-01 | P1 | PASS | 상태 변경과 렌더링 비용 분리 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-02 | P1 | PASS | 데이터 크기×이력 길이 matrix | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-03 | P1 | PASS | deep copy의 실제 프로파일 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-04 | P1 | RUNNING | 장시간 세션의 자원 증가 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-05 | P1 | PASS | Python/Rust end-to-end 비교 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-06 | P1 | PASS | 동시 render의 격리 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-07 | P2 | PASS | 작은 최적화부터 평가 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-08 | P2 | PASS | 대형 데이터 지원 범위의 명문화 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PKG-01 | P0 | PASS | 깨끗한 wheel의 코어 독립성 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-02 | P1 | PASS | optional extras의 기능 경계 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-03 | P0 | PASS | sdist와 wheel 내용·메타데이터 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-04 | P1 | PASS | 저장소 밖 CLI 실행 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-05 | P0 | PASS | 최소 지원 버전 검사 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-06 | P1 | PASS | Windows 한글·공백·긴 경로 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-07 | P1 | OPEN | GUI 없는 Linux와 OS 차이 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-08 | P1 | PASS | source-tree 편집기의 실행 안내 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-09 | P1 | PASS | lock·빌드 격리·설치 재현 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| CI-01 | P0 | RUNNING | 표준 검사 실제 실행 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-02 | P1 | PASS | 브라우저·TeX skip 가시성 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-03 | P1 | PASS | 속성 기반 상태 테스트 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-04 | P1 | OPEN | golden image의 역할과 오차 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-05 | P1 | PASS | 핵심 실패를 잡는 테스트인지 검증 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-06 | P1 | PASS | CI 지원 환경과 병렬 실행 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-07 | P0 | DEFERRED | 릴리스 버전·태그·산출물 동일성 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-08 | P1 | OPEN | 체크섬·OIDC provenance 검증 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-09 | P1 | OPEN | 공급망 권한·실패 정책 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| DOC-01 | P1 | PASS | 한글·영문·생성 문서 정합성 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-02 | P1 | PASS | public API와 오류 계약 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-03 | P1 | PASS | 발견 사항의 증거 수준 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-04 | P1 | OPEN | 릴리스 허용 조건 판정 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-05 | P2 | OPEN | 근거 기반 재평가 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-06 | P1 | OPEN | 개발자·Codex 인계 결과 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |

## 판정 범위와 다음 순서

- 현재 상태: PASS 136, RUNNING 6, OPEN 7, FAIL 0, BLOCKED 0, N/A 0, DEFERRED 1. 이는 완료율/안정성 확률이 아닙니다.
- 확인된 production 결함: FIND-002/003/004/005/006/007/008/010/011/012/013/015/017/018/019/020/021/022/024/026/028/029/030/033/034/035/036/037/038/039/040/041/042/043/044/045/046을 재현 후 수정했습니다. CI 구성 FIND-023은 별도 실행 예산 결함입니다. FIND-014는 별도의 CI fixture 설치 환경 불일치입니다. FIND-001은 연결 검사 결함, FIND-009는 요청 선행 거부 보강이며 실제 전체 body 한도 우회를 확인한 것은 아닙니다. 미검증 영역의 결함 부재를 뜻하지 않습니다.
- 다음: JSON/출력 ID의 기존 fixture 범위를 대조하고, editor/보안/Rust/패키징의 P0 경계를 증거 파일과 연결합니다. 기준을 완전히 충족한 ID만 닫습니다.
- 원문 G0~G8 gate는 전체 PASS가 아닙니다. 전체 suite·전체 최소 환경·Rust MSRV·headless Linux·TeX/성능·dependency 보안 감사·release provenance는 이번 1차 검토에서 미실행입니다.
- 비교 SHA의 clean main 실행은 별도 작업 트리/환경이 필요합니다. 현재 dirty tree를 reset/clean/revert하지 않습니다.
- 공개 계약 변경, snapshot/zero-copy 구조 변경, 원격 인증, PGF 다중 파일 원자성, 새 성능 임계값/전면 benchmark framework는 도입하지 않았습니다.
