import sys,time,tempfile,os,json,shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from script_toolbox.model import create_item
from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_sync import SyncService
from script_toolbox.core.preset_references import PresetResolver, load_preset_snapshot
root=tempfile.mkdtemp(prefix='b01-benchmark-')
registry=SourceRegistry(os.path.join(root,'prefs.json'),os.path.join(root,'cache'))
remote=os.path.join(root,'remote')
presets=[]
for i in range(500):
    folder=create_item('folder',{'id':'f'+str(i),'name':'f'+str(i)})
    folder['items']=[create_item('string',{'id':'v'+str(j),'name':'v'+str(j)}) for j in range(10)]
    presets.append({'id':'p%04d'%i,'root':folder,'label':'P%04d'%i})
publish_presets(presets,remote,'bench','Bench')
registry.put({'id':'bench','remote_path':remote})
SyncService(registry).check('bench',True)
start=time.perf_counter();resolver=PresetResolver(registry);load=time.perf_counter()-start
start=time.perf_counter()
for i in range(2000): resolver.target('bench','p0499','v9')
lookup=time.perf_counter()-start
print(json.dumps(dict(root=root,load_seconds=load,lookup_seconds=lookup,presets=500,targets=5000,lookups=2000)))

start=time.perf_counter(); snapshot=load_preset_snapshot(registry); snapshot_time=time.perf_counter()-start
reference=resolver.create_reference("bench","p0499","v9")
start=time.perf_counter()
for i in range(2000): snapshot.resolve(reference)
print(json.dumps(dict(snapshot_seconds=snapshot_time, resolve_2000_seconds=time.perf_counter()-start)))
shutil.rmtree(root)
