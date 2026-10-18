"""SEC-07: references stay data; ordinary PNG/SVG never fetch or execute them."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_PROGRAM = r"""
import json,pathlib,sys
from xml.etree import ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mudplot as mp
# Warm platform font/backend discovery before testing input-specific sinks.
base=mp.plot({'x':[1,2],'y':[2,3]}).line('x','y').size(4,3)
for extension in ('png','pdf','svg'):
    plt.close(base.save('warm.'+extension))
    pathlib.Path('warm.'+extension).unlink()
blocked=[]
def audit(event,args):
    sinks={'os.system','subprocess.Popen','pickle.find_class'}
    if event.startswith(('socket.','urllib.')) or event in sinks:
        blocked.append(event)
        raise AssertionError('unexpected input sink: '+event)
sys.addaudithook(audit)
assert mp.resolve_reference_href({'doi':'doi:10.1000/offline'})=='https://doi.org/10.1000/offline'
assert mp.resolve_reference_href({'archiveprefix':'arXiv','eprint':'2101.00001'})=='https://arxiv.org/abs/2101.00001'
assert mp.resolve_reference_href({'url':'https://127.0.0.1:9/offline'})=='https://127.0.0.1:9/offline'
bib=mp.ReferenceCatalog.from_bib_text(
    '@article{offline_key, doi={10.1000/offline}, title={data not code}}')
assert bib['offline_key'].href=='https://doi.org/10.1000/offline'
metadata=[
    {'py/object':'builtins.eval','__class__':'os.system',
     '__reduce__':['echo inert'],'path':'private.txt'},
    {'url':'https://127.0.0.1:9/not-fetched',
     'text':"__import__('os').system('echo inert')"}]
protected=pathlib.Path('private.txt');protected.write_bytes(b'private input sentinel')
plot=mp.plot({'x':[1,2],'y':[2,3],'metadata':metadata}).line(
    'x','y',label='plain <script>not executable</script>',
    citation='offline_key',href='https://127.0.0.1:9/not-fetched'
).labels(title="__import__('os').system('echo inert')").size(4,3)
encoded=plot.to_json();restored=mp.Plot.from_json(encoded)
assert restored.spec==plot.spec and restored.spec.data.columns['metadata']==metadata
assert mp.validate(restored.spec)==[]
path=pathlib.Path('reference.'+sys.argv[1]);plt.close(restored.save(str(path)))
if sys.argv[1]=='svg':
    text=path.read_text(encoding='utf-8')
    assert 'https://127.0.0.1:9/not-fetched' in text
    nodes=ET.fromstring(text).iter()
    assert not any(n.tag.rsplit('}',1)[-1]=='script' for n in nodes)
elif sys.argv[1]=='pdf':assert path.read_bytes().startswith(b'%PDF')
else:assert path.read_bytes().startswith(b'\x89PNG')
for href in ('javascript:alert(1)','data:text/html,plain','file:///private.txt','ftp://127.0.0.1/not-fetched'):
    raw=json.loads(encoded);raw['panels'][0]['layers'][0]['href']=href
    spec=mp.from_json(json.dumps(raw));issues=mp.validate(spec)
    assert any('href' in issue for issue in issues)
    try:mp.render(spec)
    except ValueError:pass
    else:raise AssertionError('unsafe href rendered')
raw=json.loads(encoded);raw['panels'][0]['layers'][0]['citation']=r'\input{private}'
assert any('citation' in issue for issue in mp.validate(mp.from_json(json.dumps(raw))))
assert protected.read_bytes()==b'private input sentinel' and blocked==[]
assert set(p.name for p in pathlib.Path('.').iterdir())=={'private.txt',path.name}
print(json.dumps({'format':sys.argv[1],'reference_resolution_offline':True,'sink_attempts':blocked,'metadata_not_restored_as_objects':True,'unsafe_links_rejected':True,'source_unchanged':True}))
"""


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_reference_and_json_strings_do_not_fetch_execute_or_restore_objects(
    tmp_path, extension
):
    result = subprocess.run(
        [sys.executable, "-c", _PROGRAM, extension],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    proof = json.loads(result.stdout)
    assert proof["sink_attempts"] == [] and proof["metadata_not_restored_as_objects"]
