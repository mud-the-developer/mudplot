# 성능과 지원 workload 범위

*[English](PERFORMANCE.md)*

제한된합성측정이지 **SLA/streaming/수백만행지원약속이아닙니다**.
[현재E2E receipt](review_evidence/e2e_performance_verification.json)에source/env/log지문을
보존하며[이전coreprofile](review_evidence/performance_verification.json)/
[replay-memory비교](review_evidence/history_improvement_verification.json)는별도실험입니다.
문서를썼다고옛측정의소스가갱신된것으로보지않습니다.

## 같은데이터/action, 다른경로

Windows11/Python3.12.15/NumPy2.5.2/Matplotlib3.11.1,4×3inch/100DPI의rawline,
3개numeric/text열/유한합성행/순차SetTitle5개를사용했습니다. 각경로의최종지원spec과
cachedPNG **pixel**은direct결과와같고잘못된layout뒤정상title도state/preview를보존·회복했습니다.

| 행수 | Direct reduce/public PNG save·close·read | Python formHTTP+PNGfetch | Rust title-formHTTP+PNGfetch |
| --- | ---: | ---: | ---: |
| 1,000 | median530ms | 561ms | 4215ms |
| 10,000 | median553ms | 597ms | 4431ms |

고비용경로표본은각5개라nearest-rankp95는관찰max이지 **안정적tail추정이아닙니다**.
Direct는atomicfilesystemI/O를포함하고editor는buffer/HTML입니다. HTTP는새loopback연결/
응답body/PNGfetch까지이며browserdecode/paint가아닙니다. Median차이를정확한networkoverhead로
빼거나겹치는componentprobe를합해가짜총비용으로만들지않습니다.

Warm은API/editor의import/server/fontcache가따뜻하다는뜻입니다. Rust는여전히정상action마다
apply·previewrender의Pythonchild2개를새로시작합니다. HTML도1k/10k에서약203KB/1.82MB이며
Python은약25KB였습니다. 언어이름만으로이혼합processpipeline의속도를예측하지마세요.

별도100표본warmprobe는1k/10k에서JSONencode약1.6/15.4ms,decode3.0/18.2ms,
reduce0.41/3.43ms,snapshot0.41/3.38ms였습니다. Rawlinevalidation약0.013ms는KDE/bootstrap/
다른algorithm비용이아닙니다. 크기마다별도3freshCLItrial의apply약1.68–1.81s/renderpreview2.55–2.83s는
process/import/I/O포함값이고HTTP에도겹쳐들어가므로합산breakdown이아닙니다.

## Cold준비는별도작업

사용자cache를지우지않고새소유font-cache디렉터리를사용했습니다. APIimport약0.59s와
첫save0.54–0.56s는Python첫statement부터이며그전interpreterlaunch는제외입니다. 새Python
서버defaultpreview준비약2.30s/Rust4.28s는초기화작업자체가다릅니다. 첫sourceopen은
Python0.54–0.60s/Rust1.80–2.01s였고readinesspoll은최대50ms를더할수있습니다.
CLIprobe는실제설정venvprocess시작/종료를포함합니다. Default준비/open/action을한개의
coldstart숫자로섞지않습니다.

## 작은최적화와정확성

DefaultpureStore는이전64action경계의내부state한개를보관합니다. 관찰한1k행/1000actionundo는
약405→17ms,10k행/256action의cached/fullreplaycontrol은약219/860ms였고추가tracedPython
retention은약280KB였습니다. 모든history/분리된publicsnapshot을유지하고customreducer는fullreplay,
이전cursor는initialfallback입니다. 추가fullSpec한개의memorytradeoff이지전체RSS/모든경로속도보장은아닙니다.

Mousegesture는이미release1요청이고keyboardburst도기존UI에서모읍니다. Coreevent/noop/listener를
없애지않습니다. 싼rawvalidation측정때문에trustboundary검증을삭제할이유가없고Rustchild시작/
JSON/render는서로다른병목입니다. 현재논문workload에immutable/zero-copyrewrite가필수라는측정은없습니다.

## 실제데이터사용안내

- 반응성이중요하면1k행/10–100action정도의논문이력부터시작하세요.10krawline도완료됐지만
  20msUI약속은아닙니다.
- 별도100k행corematrix는짧은10action을완료했으나큰targethistory는dispatchbudget에서
  미완료였습니다. 미측정undo/redo는 **null** 이지0이아니며100k×1000세션으로외삽하지않습니다.
- Typed통계/semantic은자기row/group/algorithm상한이있고여러경로는10kusable행입니다.
  Rawline측정이그제한을면제하지않습니다.
- Inline data는state와함께복사/직렬화됩니다.16MiBrequest/2000pxpreview/256panel·cell/
  총1024layer/bivariate축512/owned40Mpixel은서로다른제한이지CPU/RAM보장이아닙니다.
  [호환성](COMPATIBILITY.ko.md)/[보안](../SECURITY.ko.md)을확인하세요.
- Domain에맞는집계/preview선택은 **plot전에명시적으로** 하고원본data/spec을따로보존하세요.
  Engine은editor/export상한을맞추려고관측을몰래제거하지않습니다. 새Plot/Store는새이력으로
  시작하는명시선택이며기존undo를보존했다고하면안됩니다.

아래는순서가있는유한numericpreview의연속block평균과count입니다. 대표관측이바뀌므로
보편downsampler/원자료uncertainty대체방법이아닙니다.

```python
from statistics import mean

original = [(i, float(i * i)) for i in range(25)]
block_size = 10
blocks = [original[i:i + block_size] for i in range(0, len(original), block_size)]
preview = {
    "x": [mean(x for x, _ in block) for block in blocks],
    "y": [mean(y for _, y in block) for block in blocks],
    "n": [len(block) for block in blocks],
}
assert preview["n"] == [10, 10, 5]
assert sum(preview["n"]) == len(original)
assert preview["x"] == [4.5, 14.5, 22]
```

이평균을25개원관측인것처럼CI를계산하지말고원자료나명시적으로지원된weight/group의미를사용하세요.

### 후속설계경계

Data-store/spec분리는 **실제workload** 에서이범위이상copy/transport병목이증명됐을때의
후속설계issue입니다. StabledataID/수명/완전export/snapshot/cache무효화계약이필요하며
이번검토로새storageAPI/streamingengine/자동history절단을넣지않습니다.
