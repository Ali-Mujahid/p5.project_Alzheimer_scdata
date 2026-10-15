"""Finite source-pinned coordinate annotation; immutable strict FD guard dependency."""
import sys
sys.dont_write_bytecode=True
import fcntl,hashlib,importlib.util,json,os,signal,subprocess,traceback
from pathlib import Path
SRC=Path(__file__).resolve().parent

def need(ok,message):
    if not ok:raise RuntimeError(message)

def load(p):
    need(p.is_file() and not p.is_symlink(),'Missing/linked JSON '+str(p));return json.loads(p.read_text())

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def source(p,expected=None):
    need(p.is_dir() and not p.is_symlink(),'Missing/linked source')
    m=load(p/'source_manifest.json');pin=sha(p/'source_manifest.json')
    need(expected is None or pin==expected,'Source manifest pin differs')
    need(set(m)=={x.name for x in p.iterdir() if x.name!='source_manifest.json'},'Unexpected source members')
    for name,value in m.items():need(Path(name).name==name and not(p/name).is_symlink() and sha(p/name)==value,'Source bytes differ: '+name)
    return pin

def main():
    need(len(sys.argv)==1,'No unreviewed runtime arguments')
    policy=load(SRC/'policy.json');root=Path(policy['root']);own=source(SRC);job=os.environ.get('SLURM_JOB_ID','')
    need(job.isdigit() and not os.environ.get('SLURM_ARRAY_JOB_ID') and os.getuid()==policy['uid'] and not sys.flags.optimize,'Expected single owner allocation')
    need(SRC==root/'pre_processed_ATAC/analysis_source'/policy['source_version'],'Unexpected deployed source')
    need(Path(sys.executable)==root/'pre_processed_RNA/analysis_environment/rna_py312/bin/python','Unexpected Python')
    need(not os.environ.get('PYTHONPATH') and not os.environ.get('PYTHONHOME') and os.environ.get('PYTHONNOUSERSITE')=='1' and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','Python isolation absent')
    dep=root/'pre_processed_RNA/analysis_source'/policy['guard_dependency_version'];source(dep,policy['guard_dependency_manifest_sha256'])
    need(load(dep/'source_manifest.json')==policy['guard_dependency_members'],'FD guard exact member pins differ')
    sys.path.insert(0,str(dep))
    try:
        spec=importlib.util.spec_from_file_location('strict_peak_TE_guard',dep/'guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    finally:sys.path.pop(0)
    ctl=subprocess.check_output(['scontrol','show','job','-o',job],text=True,timeout=30);attrs=g.fields(ctl)
    need(attrs.get('JobId')==job and attrs.get('JobState')=='RUNNING' and attrs.get('UserId')=='mujahid(10796)' and attrs.get('Account')==policy['account'],'Current owner/state/account differs')
    need(attrs.get('NumNodes')=='1' and attrs.get('Requeue')=='0' and int(attrs['NumCPUs'])==8 and int(attrs['CPUs/Task'])==8 and g.memory_MiB(attrs['MinMemoryNode'])==32768 and 0<g.time_seconds(attrs['TimeLimit'])<=14400,'Require finite8CPU32GiB4h')
    need(attrs.get('Command')==str(SRC/'annotate.sbatch'),'Unexpected allocation command')
    base=root/'pre_processed_ATAC/analysis_runs'/policy['source_version'];base.mkdir(parents=True,exist_ok=True)
    need(not base.is_symlink(),'Output stage namespace is a symlink')
    need(not(base/'stage.lock').is_symlink(),'Stage lock is a symlink')
    need(not(base/'execution.once.json').is_symlink(),'Execution intent is a symlink')
    lock=(base/'stage.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=base/('job-'+job);out.mkdir(exist_ok=False);(out/'tmp').mkdir()
    try:
        with (base/'execution.once.json').open('x') as f:json.dump({'job_id':job,'source_manifest_sha256':own,'operator':'Codex under human full authorization','scope':'coordinate annotation only'},f)
        def interrupted(sig,frame):raise RuntimeError('Parent interrupted '+str(sig))
        for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,interrupted)
        os.environ.update(TMPDIR=str(out/'tmp'),MPLCONFIGDIR=str(out/'tmp/matplotlib'),MPLBACKEND='Agg',OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8',NUMBA_NUM_THREADS='8')
        registry=g.OwnedFDRegistry(out,policy);g.save(out/'quota_before.json',g.quota(policy));first=g.sample(root,out,registry,policy,'admission')
        g.save(out/'started.json',{'utc':g.utc(),'job_id':job,'controller':ctl,'source_manifest_sha256':own,'guard_dependency_manifest_sha256':policy['guard_dependency_manifest_sha256'],'shared_usage':first['shared_usage'],'normalization_ready':False,'raw_matrix_read':False})
        g.monitored([sys.executable,'-B',str(SRC/'test_annotation.py')],root,out,registry,policy,'fixture.log','generated_coordinate_annotation_tests',180)
        need(('Ran '+str(policy['required_tests'])+' tests') in (out/'fixture.log').read_text() and '\nOK\n' in (out/'fixture.log').read_text(),'Exact generated test gate absent')
        g.monitored([sys.executable,'-B',str(SRC/'annotate.py'),str(SRC/'input_catalog.json'),str(out/'annotation')],root,out,registry,policy,'annotation.log','all_hit_RMSK_coordinate_annotation')
        result=load(out/'annotation/coordinate_complete.json')
        need(result['status']=='coordinate_annotation_complete_descriptive_coverage_only' and result['peak_groups']==467 and result['common_consensus_peaks']==68126 and result['all_repeat_overlaps_preserved'] is True,'Coordinate completion failed')
        for name in ['normalization_ready','TE_expression_measured','TE_fragment_accessibility_measured','raw_matrix_read','final_cell_types_assigned','inferential_enrichment','p_values_or_FDR']:need(result[name] is False,'Unreviewed scientific scope '+name)
        g.monitored([sys.executable,'-B',str(SRC/'plots.py'),str(out/'annotation')],root,out,registry,policy,'plots.log','animal_level_descriptive_peak_repeat_plots')
        plots=load(out/'annotation/plots_complete.json');need(plots['status']=='descriptive_animal_level_peak_repeat_plots_complete' and plots['all_cell_types_preserved'] is True and plots['normalization_ready'] is False,'Plot completion failed')
        need(not registry.live_descendants(),'Known live/unknown descendants remain');source(SRC,own);source(dep,policy['guard_dependency_manifest_sha256']);g.save(out/'quota_after.json',g.quota(policy))
        products={str(p.relative_to(out)):{'path':str(p),'bytes':p.stat().st_size,'inode':p.stat().st_ino,'mtime_ns':p.stat().st_mtime_ns} for p in (out/'annotation').rglob('*') if p.is_file()}
        g.save(out/'execution_complete.json',{'utc':g.utc(),'job_id':job,'returncode':0,'source_manifest_sha256':own,'normalization_ready':False})
        g.save(out/'complete.json',{'utc':g.utc(),'job_id':job,'returncode':0,'source_manifest_sha256':own,'guard_dependency_manifest_sha256':policy['guard_dependency_manifest_sha256'],'coordinate_receipt_sha256':sha(out/'annotation/coordinate_complete.json'),'plots_receipt_sha256':sha(out/'annotation/plots_complete.json'),'input_checksums_sha256':sha(out/'annotation/input_checksums.actual.json'),'outputs':products,'normalization_ready':False,'final_types':False,'TE_expression_measured':False,'TE_fragment_accessibility_measured':False})
        final=g.sample(root,out,registry,policy,'after_final_receipts');g.save(out/'storage_complete.json',final['shared_usage'])
    except BaseException as e:
        g.save(out/'failed.json',{'utc':g.utc(),'job_id':job,'error':repr(e),'traceback':traceback.format_exc(),'normalization_ready':False});raise
    finally:lock.close()

if __name__=='__main__':main()
