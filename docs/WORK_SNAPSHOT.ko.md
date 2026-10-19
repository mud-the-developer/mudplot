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

- 최신공유htmx/license/nativebrowserhash·4controlledversion·metadata거절과관련176/
  floor2로RUST-07은matching-source범위PASS입니다. Runtimepackagehandshake를추가하지
  않았고전체표준smoke의outertimeout은focused성공과구분해미확인으로남깁니다.
  489aCI의즉시focusassert실패는성공이아니며boundedfocuswait수정의로컬4통과/새LinuxCI
  필요를구분해대기HTML/자산/testfix를함께게시합니다.

- 최신FIND-042는action/focus정책을바꾸지않고erroralert/currentpage의미를붙입니다.
  새pure3/실제keyboard-only·관련169/browser6/floor3로EDIT-08은Python범위PASS이며
  EDIT01..09검토가사람의AT/nativecontrol인증은아닙니다. 긴Tab경로는명시하고489aCI
  39183500953중HTML효과는로컬보존해이전CI를새수정증거로소급하지않습니다.

- 최신FIND-041은decoder오류에공개fieldcontext를추가하고오류종류/union허용은유지합니다.
  새9/관련386/OS2skip·실제CLI/UI/native26·browser3/floor9로EDIT-07/09는범위PASS이지
  보편redactor/새RPC는아닙니다. 정확한B9CI5job성공으로이전040전체를확인했고세대기unit을
  게시해새decoder소스전체CI를받습니다. 버전/의존성/배포는유지합니다.

- 최신valid/bad/valid파일과SVGsavefault의실제UI는state/history/draft/자원을보존하고
  정상편집/export/다운로드로회복하며원파일은불변입니다. 관련229/OS6skip·browser4/floor43로
  EDIT-06은지원범위PASS입니다. Runtime없이newB9CI39178688403중확대+회복검증은로컬
  보존하고더넓은오류/agent정책은별도남깁니다.

- 최신ChromiumDPR/CSS/visual-viewport3case는highDPIpreview의dataframe/키/focus/undo/
  redo와편집DPI600을유지합니다. 관련178/실제browser8/floorpure7로EDIT-02는emulation범위
  PASS이지모든hardware보장은아닙니다. Runtime변경없고정확한4bcCI5job성공뒤D535+B9를
  게시해newB9CI39178688403진행중이며현재확대test/doc은로컬보존합니다.

- 최신공유session은두tab/rawaction도착과직렬commit에서field유실/부분preview가없고
  순수state/새PNG가맞습니다. 관련169/OS1skip·실제browser4/floor8로EDIT-05는로컬범위
  PASS이지live협업/tab별panel은아닙니다. 새runtime없이4bcCI중대기응답효과와test/doc을로컬보존합니다.

- 최신FIND-040은로컬UIreplygeneration으로늦은옛HTML이최신inspector를덮지않게합니다.
  Spec/historyrevision신설없이실제DOM/spec/previewpixel과관련179/browser8/floor2/
  activeLSP5clean이맞아EDIT-03/04는지원범위PASS입니다. 요청은commit되고서버재시작뒤
  page새로고침의한계는남깁니다. 4bcCI중효과unit을로컬보존하며이전CI를소급하지않습니다.

- 최신FIND-039는Pythoneditory2datahandle이primaryy범위/scale을쓰던문제를고쳤습니다.
  15frame/newpure5/browser1·관련209/OS1skip·실제browser6/floor17이통과해primary/title/
  legend뜻과undo/redo를유지하며PLOT-11은지원범위PASS입니다. PLOT전체검토가nativeparity는
  아니며기준b8CI5job모두성공뒤alpha+좌표runtime을게시해새전체CI를받습니다.

- 최신FIND-038은공통branch에서annotationtext/arrowopacity누락을고치고defaultRGBA/
  nativeclip/zorder를유지합니다. 수작업overlay와alpha0pixel이맞아관련245/floor12/
  activeLSP3clean으로PLOT-09/12는범위내PASS입니다. PLOT-11drag좌표는별도로남기고
  b8CI의Rust/min성공·양Pytest진행을보호해효과unit은로컬보존합니다. 이전CI는새alpha증거가아닙니다.

- 최신shared/log9축표/3충돌·지원영역은선택214/floor214가통과했습니다. 1841Pyparsing과
  2MPL3.8image경고를구분해pixel/Werror대조로RGB/원자료/이전출력을확인했고PLOT-05/10은
  범위내PASS이지모든극단범위보장은아닙니다. 기준3bCI39166807390의5job모두성공해수치
  효과runtime전체검증을확인했습니다. 세문서unit을게시하며여기서code/버전/lock/배포는바꾸지않습니다.

- 최신12role별원행추적은value/weight/unit대응과필수값거절을유지합니다. 경계선택388/
  floor388·분류한Pyparsing489경고로STAT-08은범위내PASS이며STAT01..08의명시corpus검토를
  마쳤지만보편통계/API인증은아닙니다. Runtime/newtest없이3bCI양Rust성공/3Python진행을
  보호해분포+pairing문서는로컬보존합니다.

- 최신수작업8box/24violin과seed0jitter순서·새process·hash/RNG가일치합니다. 관련408/
  floor407·분류한Pyparsing1649경고로STAT-06/07은지원범위PASS이며새runtime/randomAPI/
  testframework는없습니다. 3bCI양Rust성공/3Python진행을보호해문서는로컬보존하고이전수치효과의
  정확한새전체CI결과는아직남아있습니다.

- 최신KDE기존285/독립mixture24·두modegrid는bandwidth/PDF/CDF/꼬리/퇴화를대조해
  관련359/floor285가통과했고317경고는재실행해모두Pyparsing으로분류했습니다. STAT-05는
  지원범위PASS이지새kernel/fallback은아닙니다. 기준efCI5job모두성공해수치/histogram/KDE를
  함께게시하고새효과소스CI를받습니다.

- 최신histogram은기존186case/독립Decimal38행으로weights/경계/분모/면적/CDF/geometry/
  출력을대조했습니다. 관련269/floor186·257경고모두Pyparsing분류로STAT-04는범위내PASS이며
  runtime/newtest변경없이efCI마지막3.10Pytest/다른4성공을보호해수치+문서를로컬보존합니다.

- 최신FIND-037은legacycovarianceunder/overflow와rank/산술경계를공통helper에서고쳐
  독립OLSmean-fitband/원단위/파일복구를유지합니다. 관련201/floor19로STAT-03은범위내
  PASS이지모든거대축렌더보장은아닙니다. efCI중효과unit은로컬보존합니다.

- 최신quiver/3D/polardata좌표와scalardomain/mask/colorbar·numericlegend검사는관련229/
  floor12가통과해PLOT-07/08이현재지원조합PASS입니다. 새API/schema/runtime없이기준b777
  4성공/마지막sitebuild진행을보호해준비감사+projection단위를로컬보존합니다.

- 최신준비inventory는5synthetic입력/42공유JSON결과snapshot/private로그를분리하고제한된
  scan한계를명시합니다. 계약충돌표는기존선택/이유이지새승인이아닙니다. 기존313/품질7이
  통과해BASE-06/07은범위내PASS이며보편privacy인증은아닙니다. BASE-05는남기고b777CI중문서는로컬보존합니다.

- 최신격리drift/복구회귀는실제syncchecker와action36/layer37등록표를대조합니다.
  관련231/floor4가통과해JSON-11은범위내PASS이며runtime/generatedbytes/schema강화는
  없습니다. BASE/nullable감사는별도로남기고161CI중test/doc은로컬보존합니다.

- 최신Windowsreadonly/locked·ENOSPC/확장자실패는bytes/staging/Figure를보존합니다.
  성공open/callerclose/weakref·80effect자원시계열과관련128/OS6skip/floor17이통과해
  OUT-04/05는bounded범위PASS이지모든ACL/장시간native누수부재인증은아닙니다.
  Runtime변경없이161CI중test/doc은로컬보존합니다.

- 최신유한pattern/범례와1-column컬러/흑백검토는명도와범주구분을분리합니다. 작은mark/
  투명band6개의한계를남기고문구/gallery의무제한구분보장을지웠습니다. 관련77/site9/floor8통과로
  COLOR-06/07/09/10은검토범위PASS이지printer/observer인증은아닙니다. 기준16aCI가전부성공해
  대기report/doc/gallery를게시하고새CI를받습니다.

- 최신HEXreport/mappedfloat명도수정은생성색을유지하고평가CVD조건과nominal/output차이를
  드러냅니다. Reference/N±1/tie/독립process와관련141/floor18이통과해COLOR-03/04/05/08은
  측정범위PASS이지인증이아닙니다. 이전report보류는16aCI완료를보호했고후속색상검토는위와같습니다.

- 최신전체rc복구/번갈아style/독립process대조로LAY-08은같은ambient조건에서PASS입니다.
  0.02inchpad가150/300DPI차이를줄이지만75DPIdense잔차는남아LAY-09는RUNNING입니다.
  관련88/floor6통과·품질8명령이며source/state/vector크기는유지합니다.
- 기준5caCI39142799672는5job전부성공했지만queuedguide/pad이전이라함께게시해새CI를받습니다.

- 최신복합guidebbox/실제renderer검사는y2label/outsidelegend겹침과같은명시ungrouped
  point/lineidentity반복을해소했습니다. 관련185/floor14통과이며rawidentity/수동anchor/
  fixedcanvas/불가능경고는유지해LAY-05는범위내PASS입니다. 이전로컬보존으로5caCI완료를보호했습니다.

- 최신실제fontfile/glyphindex/bbox가한글지원·minus/family부재·weightfallback진단을
  구분합니다. 한글/긴그룹bbox와기존지원·경고corpus로LAY-04/07은범위내PASS이며
  관련97/floor5통과입니다. 모든systemtypography가아니며runtime치환/다운로드도없습니다.
  대기layout단위와함께게시합니다.
- 기준66feCI39139498998은5job모두성공했지만새layout변경이전이라다음CI가필요합니다.

- 최신자동layout은title/suptitle/namedlegend의남은경계/겹침을경고하고음수solverrect를
  피합니다. CLI/warning-as-error가canvas/정리를유지하며관련145/floor9가통과해LAY-06은
  PASS입니다. 당시LAY-04의부분corpus는위후속CJK관찰이보완하되보편가독성보장은아닙니다.
- 이전805floor/양native는성공했지만matrix는알려진platformtype실패로끝났습니다.
  Hotfix/preset66feCI는이제성공했으나나중layouteffect에소급하지 않습니다.

- 최신5TeXpreset×2columns×2fraction의20행에서양preview와실제PNG/PDF/SVGbox가
  맞았습니다. 기존size/style우선을명시하고runtime교정은유지해LAY-03은registry범위PASS입니다.
  관련58/floor24통과·품질8명령을기록했고이전floor완료뒤hotfix/preset을함께게시했습니다.

- 최신805CI실패는추출Windowsfactory의LinuxPyright2오류이며renderer/test실패가
  아닙니다. 명시platformguard로복구하고양targetglobal검사0·runtime4통과/OS1skip을
  확인했지만새Linux실행/CI는필요합니다. Toolinghotfix는이제게시됐습니다.

- 최신HTML/SVG literal/draft decode-once·양raweditor4payload가데이터를유지하고active
  node를추가하지않았습니다. 명시trustedPGFescaping/math도컴파일돼OUT-09는범위내PASS이며
  untrustedTeXsandbox/모든font보장은아닙니다. 관련72/최소6통과·현재185upstream경고분류를기록했습니다.
- 기준06dCI39131994074는5job모두성공했습니다. 대기도구/test의local검증과함께게시하되
  후속CI도정확한현재commit의결과로판단합니다.

- 최신 reference출력은 라벨/링크를 지우지 않고 날짜/ID가결정적이며 PGF이동/누락/
  실패와4실제TeX/bibliography 조합도 통과했습니다. PDF참조번호·각5embeddedfont·
  DOIannotation을 확인해 OUT-02/06/07/08은 범위내PASS입니다. 관련70통과/no skip·
  최소6통과이며PGF비트랜잭션/OS/font한계는유지합니다. 앞선로컬보존은06dCI완료까지유지했습니다.

- 최신137초 세션은 GC후Figure0/고정handle·temp를 확인하고 의도한 history/cache를
  구분했습니다. RSS/native lifetime은 긴 관찰이 남아 PERF-04는 RUNNING입니다.
- Sampler 자체의 ctypes 타입 재생성이 no-render20회에서 객체662증가를 만들었습니다.
  Binding/type 재사용으로 고치되 PID 값/handle을 cache하지 않고 전체 세션을 다시
  실행했습니다. 관련63/OS2skip·품질/packaging6명령 통과, 제품renderer/state 변경은
  없으며앞선도구게시보류는06dCI완료까지유지했습니다.

- 최신 소유 Matplotlib effect는2serial/concurrent 출력 불일치 뒤 공통 재진입 직렬화를
  사용합니다.3format exact hash·독립session preview/layout·중첩 호출과 관련231/site9/
  최소6검사가 통과해 PERF-06은 소유 호출 범위에서 PASS입니다. 외부 Figure/pyplot은
  caller가 조정해야 하며 처리량 보장은 아닙니다. 단위는31eCI 중 로컬 보존합니다.

- 최신 독립worker rows×history는6목표 완료·3개 조합 시간예산 중단이며 unknown undo/redo는
  null로 보존합니다. Core PID RSS/peak 관찰이지 전체앱/renderer/hard-limit 보장은
  아닙니다. PERF-02는 범위 내 PASS, 관련62통과/OS2skip·품질/packaging6명령도 통과했습니다.
  Replay/alias 구조는 유지하며 새script/test/doc은31eCI 중 로컬 보존합니다.

- 최신 renderer는 지원 빈 marker/style을 자동값으로 바꾸지 않습니다. 대표20case의
  schema/Python/CLI/typedRust·양rawJSON editor40회가 일치했지만 다른 nullable 의미는
  남아 JSON-09는 부분 검증입니다. 관련266·최소79·native22통과이며 기존0/default는 유지합니다.
- 기준ea1CI39125371498은5job 모두 성공했습니다. 새 token 수정 이전 결과라 현재
  원격 검증으로 소급하지 않고 대기 성능/fixture 단위와 함께 게시합니다.

- 최신 bounded warm1천/1만/10만 행 측정은 core편집/JSON/render를 분리합니다. Title
  dispatch median0.803/6.993/67.867ms·별도 profile의 copy지배를 확인해 PERF-01/03은
  PASS입니다. 모든 hardware/latency 보장이 아니며 새script만 추가하고 core/alias 안전성은 유지합니다.
- 정확한ea1의 Linux/Windows foreground 자손·MSRV가20/21통과(helper5/6ignored)해
  RUST-04는 non-detached policy에서 PASS입니다. 앞선 게시 보류는 그 full CI 완료까지 유지했습니다.

- 최신 foreground 자손 timeout은 보유 Windows tree/새Unix group·정리 도구2초 예산과
  정리 실패 진단을 유지합니다. Windows21통과/helper6ignored·정상 native bridge는
  통과했으며 위 후속 원격 Unix/MSRV가 지원 범위를 확인했습니다. Detached worker는 미지원입니다.
- 기준e728CI39122032427은5job 모두 성공했습니다. 새 cleanup runtime 이전 결과라
  소급하지 않고 대기 로컬 단위와 게시한 뒤 새로운 CI로 CI-01을 판단합니다.

- 실제e728 Linux floor2872통과/26선택·TeXskip/경고3906을 완료했습니다. 정확한 소스와
  완전한 skip 요약이4staging symlink 통과를 뒷받침하고 양native19통과/helper3ignored/
  HTTP path도 확인해 SEC-06은 관찰 정책 범위에서 PASS입니다. Sandbox/모든OS 보장은
  아니며 앞선 full Python2job은 이제 성공했습니다. 나중 privacy/cleanup 변경은 구분합니다.

- 최신 양 editor 기본 stdout/stderr에 합성 입력 marker/traceback이 없고 state/PNG를
  보존했습니다. 같은 client draft/진단 응답은 의도된 편집 기능입니다. Runtime 변경 없이
  관련211·최소1통과이며3Python-lock/69Cargo-registry OSV snapshot의 알려진 advisory는
  없습니다. SEC-08은 범위 내 PASS이지 보안 인증은 아닙니다. 게시 보류는 기준 CI 완료까지 유지했습니다.

- 최신 full/floor 분리는 ordered60파일 floor와 full/browser/Rust 범위를 유지하며
 3Python job 각60분·Rust2job 각20분의 유한 예산을 둡니다. 같은 TeX/system-font
  전제·timing을 보존하고 CI/릴리스7통과·핵심floor39통과/4skip을 확인했습니다.5job
  원격 완료는 아직 아니며 대기 소유권/문서와 게시한 뒤 CI-01을 판단합니다.

- 최신 staging 소유권·고정 HTTP path/query와 일반PNG/PDF/SVG offline sink가 통과했습니다.
  관련128통과/OS6skip·최소80통과/권한4skip은 한정 범위이며 보안 인증/sandbox 보장은
  아닙니다. 당시 local symlink skip은 위 후속 Linux 결과가 확인했으며 SEC-07도 PASS입니다.
- 기준621CI는3.10Pytest 성공 뒤 최소환경 중1h 한도로 취소됐고 다른3job은 성공했습니다.
  검사를 줄이지 않고 floor의 별도 유한 job을 구성했으며 이전 취소 결과를 green으로 세지 않습니다.

- 최신 WindowsTMP12대조가 관찰 venv 시작 한계를 core/capture와 구분했습니다. 같은
  interpreter의 짧은TMP/긴TEMP bridge·한글/긴source 보존과 관련47개가 통과했습니다.
  PKG-06은 이 지원 host 구성/명시 한계에서 PASS이며 모든 긴 경로나 일반 자손 정리
  보장은 아닙니다. 그 앞선 진단은 runtime을 바꾸지 않았습니다.

- 최신 locked43package/반복 sync·별도 PEP517 backend·관찰한 동일55member wheel과
  새 무의존 consumer가 통과했습니다. Matching source 두 editor도 공유 자산과 함께
  시작해 PKG-08/09는 PASS입니다. Runtime 변경·릴리스 승인·모든 bytes 재현 보장은 아닙니다.
  앞선 문서 게시 보류는 기준621CI가 끝날 때까지 유지했습니다.

- 최신 optional 관련82·최소11통과/경고13과 설치 wheel7점진 extra 단계/98CLI가
  통과했습니다. 기대한 missing module만 설치 extra를 안내하고 browser package/binary는
  구분해 PKG-02/04는 PASS입니다. 무관한 import 진단은 유지합니다.
- 기준e14CI39111782233의4job은 모두 성공했지만 후속 guard의 새 통합 검증은 필요합니다.
  짧은 CWD의93/336문자 파일·lock은 통과했으나 long-CWD console·longTEMP bridge
  한계는 위의 후속 TMP control로 구분했습니다.

- 최신249field/marker+169연결 검사·최소174통과/경고13과 native18경계가 통과했습니다.
  명시 marker0을 유지하고139nullable schema/Python 의미도 확인했습니다. JSON-09의
  넓은 언어 간 의미 대조는 남기고 JSON-12는 제한 API/CLI/HTTP 복구 corpus에서 PASS입니다.
- 기준063CI는3.10의45분초과 annotation을 확인했고 양 Rust/3.12는 성공했습니다.
  전체 검사는 유지해 다음 유한60분/느린25개 측정을 구성했습니다. 완료된 기준 실행을
  더 기다리지 않고 로컬 두 단위를 게시하되 릴리스/tag는 아닙니다.

- 최신 core 대상195통과이며 신규35case는 현재/최소 환경에서 통과했습니다. Bool/
  noninteger layer index의 다른 대상 선택/TypeError를 막고 새 프로세스 hash와 효과 경계도
  확인했습니다. 기준063CI가 끝나기 전까지 게시를 보류했습니다.

- 최신 native19통과/helper3ignored·출력14경계가 통과했습니다. 빈 render commit을
  차단하고 optional 부재/실패 시 spec/PNG/redo/복구를 확인해 RUST-03은 PASS입니다.
  Timeout 자손 소유권 RUST-04는 미완료이며 이전 preview6case는 기존 범위를 유지합니다.

- 최신 데이터/JSON 대상 **291통과**, 최소 **61통과/경고201**, additive-capability를
  포함한 native **16통과/helper1ignored**입니다. 혼합 raw ID의 문자열 추론을 제거했습니다.
  아래의 넓은 과거 결과는 후속 renderer 변경 이전이며 현재 JSON-09/12는 위 상태를 따릅니다.

- 로컬 optional 전체 **3423통과/OS조건2skip/경고1** 뒤 QA-only contour API/최소
  환경 banner를 고쳤습니다. 수정된 신규72개는 현재/최소 stack에서 다시 통과했으며
  이전 전체 실행을 후속 QA까지 검증한 새 실행으로 바꾸지 않습니다.
- 최소53파일은 중복 없는8배치로 **2573통과/선택25skip**이며 단일 순서 실행과 다릅니다.
  실제 무의존 wheel을 저장소 밖 uv venv에 설치해 core·console/module CLI도 확인했습니다.
- 이전 이력199/browser32와 다른 집중 결과는 각각의 과거 범위로 유지합니다.
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
- [P0 통합 증거](review_evidence/completion_p0_verification.json)에 독립 수학/좌표/출력·
  최소 배치·실제 설치 artifact·기준92238f3 CI 성공을 연결하고 중단 시도는 제외했습니다.
- [데이터/JSON 정책 근거](review_evidence/data_json_policy_verification.json)에 그룹 식별·
  empty/singleton/행 순서·구조 JSON 검사를 연결했습니다.
- [Bridge/preview 근거](review_evidence/bridge_preview_verification.json)에 실패 출력 제한과
  실제 native preview/session 계약을 기록했습니다.
- [Bridge 실패 근거](review_evidence/bridge_fault_verification.json)에 격리 주입과
  기준fe4449d CI cancelled(양 Rust/3.12 성공,3.10 취소)를 기록했습니다. 후속 guard의 증거는 아닙니다.
- [Core 경계 근거](review_evidence/core_boundary_verification.json)에 참조/타입 오류·
  새 프로세스 hash·현재/최소 검사를 기록했습니다.
- [JSON 의미 근거](review_evidence/json_semantics_verification.json)에139field 표·
  marker 전달·제한 손상 입력 복구·CI timeout을 기록했습니다.
- [설치 matrix 근거](review_evidence/installed_matrix_verification.json)에 실제 extra·
  wheel/source hash·외부 CLI·제한된 Windows 경로 결과를 연결했습니다.
- [격리/source 편집기 근거](review_evidence/isolation_source_editor_verification.json)에
  lock·허용 범위 drift·격리 backend·실제 matching-source 시작을 구분했습니다.
- [WindowsTMP 경계 근거](review_evidence/windows_tmp_boundary_verification.json)에
  interpreter/capture/환경 대조와 같은 interpreter bridge 결과를 기록했습니다.
- [File/sink 근거](review_evidence/file_sink_verification.json)에 staging 소유·route·
  offline sink와 별도 CI 실행 예산 소진을 기록했습니다.
- [CI floor 분리 근거](review_evidence/ci_floor_split_verification.json)에 같은 범위/
  전제와 로컬 runner/핵심 subset 결과를 기록했습니다.
- [Privacy/advisory 근거](review_evidence/privacy_audit_verification.json)에 기본
  합성 log probe·정확한 lock snapshot과 audit 한계를 기록했습니다.
- [원격 floor/native 근거](review_evidence/remote_floor_verification.json)에 완료job
  log hash·skip 범위·소스 기반 symlink 판단 근거를 보존합니다.
- [자손 정리 근거](review_evidence/descendant_cleanup_verification.json)에 controlled
  Windows timeout/실패/복구와 한계·변경 이전 CI 성공을 기록했습니다.
- [성능 근거](review_evidence/performance_verification.json)에 단계별 median/p95/
  반복수·별도 Python 할당/profile 한계를 보존했습니다. [현재 원격 정리](review_evidence/remote_cleanup_verification.json)는
  양OS 정확한 소스/MSRV/control을 확인하되 전체job 완료로 확대하지 않습니다.
- [Render-token 근거](review_evidence/render_token_verification.json)에 명시 정규화/
  CLI/codec/rawUI 범위와 남은 전 필드 의미 격차를 보존했습니다.
- [이력비용 근거](review_evidence/history_cost_verification.json)에 완료/중단 목표·
  정확한 예산/RSS 범위와 checkpoint 오류 회귀를 보존했습니다.
- [소유동시성 근거](review_evidence/concurrent_render_verification.json)에 exact
  serial/concurrent bytes·현재/최소검사와 소유권 한계를 보존했습니다.
- [세션 자원 근거](review_evidence/session_resource_verification.json)에 실제RSS/
  handle/Figure/cache와 observer 자체 증가를 구분했습니다.
- [출력/참조 근거](review_evidence/output_reference_verification.json)에 hash/
  compiler·JUnit·sidecar검사와 실제 PDFfont/URI 관찰을 보존했습니다.
- [문자열문맥 근거](review_evidence/string_boundary_verification.json)에 정확한
  HTML/SVG값·실제trustedTeX컴파일·현재warning분류를보존했습니다.
- [Platformguard 근거](review_evidence/platform_guard_verification.json)에 정확한
  실패CIstep과별도currentplatform검사를기록했습니다.
- [Presetgeometry 근거](review_evidence/preset_geometry_verification.json)에 실제
  filebox·TeX단위정의·현재size/font우선순위를기록했습니다.
- [Layout경계 근거](review_evidence/layout_boundary_verification.json)에before/after
  bbox·행동가능warning·CLI/rollbackcontrol을기록했습니다.
- [Font경계 근거](review_evidence/font_boundary_verification.json)에 실제family/
  glyph/bbox진단을폰트binary나보편보장없이보존했습니다.
- [복합guide 근거](review_evidence/mixed_guide_verification.json)와
  [visualbaseline](review_evidence/mixed_guides_baseline.png)에bbox/renderer event를보존했습니다.
- [Style/DPI 근거](review_evidence/style_dpi_verification.json)에rc/hash·물리padding과
  명시한저DPI잔차를보존했습니다.
- [Palette report근거](review_evidence/palette_report_verification.json)에최종RGBpair/
  model·표현조건·범주경계를보존했습니다.
- [Encoding/print근거](review_evidence/encoding_print_verification.json)와
  [comparison](review_evidence/one_column_encoding.png)에pattern/물리설정/한계를보존했습니다.
- [Outputlifecycle 근거](review_evidence/output_lifecycle_verification.json)에OS실패와
  bounded소유권/RSS/handle관찰을보존했습니다.
- [Generateddrift 근거](review_evidence/generated_drift_verification.json)에실제
  checker실패/복구·registrycoverage를보존했습니다.
- [Review준비](REVIEW_PREPARATION.md)와 [inventory](review_evidence/preparation_audit_verification.json)에
  fixtureconsumer/evidence범위/계약결정을보존했습니다.
- [Projection/colour 근거](review_evidence/projection_colour_verification.json)에
  독립좌표/명시범위/미지원경계를보존했습니다.
- [Regression경계 근거](review_evidence/regression_degenerate_verification.json)에
  before/after·design조건수/rank·독립OLS공식을보존했습니다.
- [Histogram 정규화 근거](review_evidence/histogram_normalization_verification.json)에
  독립bin/질량/면적과현재warning분류를보존했습니다.
- [KDE 적분 근거](review_evidence/kde_integral_verification.json)에정확moment/
  유한support질량/singular·clip경계를보존했습니다.
- [Distribution/jitter 근거](review_evidence/distribution_jitter_verification.json)에
  수작업/pairedrow/정규화식과process/RNG/hash범위를보존했습니다.
- [Observationpair 근거](review_evidence/observation_pairs_verification.json)에원래
  index/필수role/정확mean/거절정책을보존했습니다.
- [Axisdomain 근거](review_evidence/axis_domain_verification.json)에panel별설정/
  log결과와실제backend경고한계를보존했습니다.
- [Overlay/alpha 근거](review_evidence/overlay_alpha_verification.json)와
  [제한비교](review_evidence/annotation_alpha.png)에실제pixel/style경계를보존했습니다.
- [Coordinateframe 근거](review_evidence/coordinate_frame_verification.json)에
  축별metadata/실제browserdrag/이전상태경계를보존했습니다.
- [Response순서 근거](review_evidence/response_order_verification.json)에실제
  전달/commit/DOM/pixeltimeline과내부generation범위를보존했습니다.
- [Sharedsession 근거](review_evidence/shared_session_verification.json)에
  요청/commit순서·허용결과·최종cache/spec동등성을보존했습니다.
- [Scaledpreview 근거](review_evidence/scaled_preview_verification.json)에실제
  viewport/DPR설정·pointer/data·원DPI/state를보존했습니다.
- [Editor회복 근거](review_evidence/editor_recovery_verification.json)에
  spec/PNG/history/오류hash·소스보존·export회복을보존했습니다.
- [Machine/오류 근거](review_evidence/machine_error_verification.json)에실제
  route/status/type/error표와numericfieldcontext경계를보존했습니다.
- [Keyboard/access 근거](review_evidence/keyboard_access_verification.json)에
  Tab횟수·실제pointer0경로·의미/focus검토범위를보존했습니다.
- [Editorasset 근거](review_evidence/editor_asset_verification.json)에
  served/compiledhash·controlledmismatch·미확인smoke를보존했습니다.
- [150-ID 리뷰 대장](REVIEW_CHECKLIST_STATUS.md): **PASS123/RUNNING5/OPEN21/DEFERRED1**.
  CI-01은 새 통합 CI 전 진행 중이며 release-only CI-07은 보류입니다.
  미검증 항목을 통과로 취급하지 않습니다.

이전 기능/최소환경/브라우저 결과는 각자의 범위이며 후속 변경 이전 결과입니다.
이를 현재 전체 작업 트리의 검증으로 확대하지 않습니다. 전체 Python/최소환경 matrix,
Rust MSRV·Linux/TeX·의존성 보안 감사·성능·릴리스 provenance gate는 미완료/보류입니다.

지원 범위와 제한은 [구현 계획](V1_1_PLAN.ko.md), [기능표](FEATURE_COVERAGE.ko.md),
[Unreleased 변경 이력](../CHANGELOG.md)을 확인하세요.
