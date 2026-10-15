"""Finite allocation wrapper for additive graph resolution1 and real marker summaries."""
import sys
sys.dont_write_bytecode = True
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import time
import traceback

SRC = Path(__file__).resolve().parent


def need(condition, message):
    if not condition: raise RuntimeError(message)


def load(path): return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def source_check(source, expected=None):
    manifest = source / 'source_manifest.json'
    need(manifest.is_file() and not manifest.is_symlink(), 'Source manifest missing/symlink')
    observed = sha(manifest)
    if expected: need(observed == expected, 'Pinned source manifest changed')
    records = load(manifest)
    for name, digest in records.items():
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'Invalid source manifest path')
        path = source / relative
        need(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(source.resolve())
             and sha(path) == digest, 'Source changed: ' + name)
    return observed


def input_check(record):
    path = Path(record['path']); info = path.stat()
    need(not path.is_symlink() and info.st_size == record['bytes'] and info.st_ino == record['inode']
         and info.st_mtime_ns == record['mtime_ns'], 'Accepted input identity changed: ' + str(path))


def seconds(value):
    match = re.fullmatch(r'(?:(\d+)-)?(\d+):(\d+):(\d+)', value)
    need(match is not None, 'Actual TimeLimit is not finite HH:MM:SS')
    days, hours, minutes, sec = [int(v or 0) for v in match.groups()]
    return days*86400 + hours*3600 + minutes*60 + sec


def MiB(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([KMGT])?', value)
    need(match is not None, 'Actual allocated memory is not finite')
    number, unit = match.groups()
    return float(number) * {None:1, 'K':1/1024, 'M':1, 'G':1024, 'T':1024*1024}[unit]


def terminate(child):
    if child is None or child.poll() is not None: return
    try:
        os.killpg(child.pid, signal.SIGTERM); child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL); child.wait()
    except ProcessLookupError:
        child.wait()


def own_usage(out, child, limits):
    seen, total, count = set(), 0, 0
    for directory, _, files in os.walk(out):
        for path in [Path(directory), *[Path(directory)/name for name in files]]:
            try: info = path.stat()
            except FileNotFoundError: continue
            key = (info.st_dev, info.st_ino)
            if key not in seen:
                seen.add(key); total += max(info.st_size, info.st_blocks*512); count += 1
    pids = [child.pid] if child is not None and child.poll() is None else []
    for pid in pids:
        try: pids.extend(int(x) for x in Path(f'/proc/{pid}/task/{pid}/children').read_text().split())
        except FileNotFoundError: pass
    for pid in pids:
        try: fds = list(Path(f'/proc/{pid}/fd').iterdir())
        except FileNotFoundError: continue
        for fd in fds:
            try:
                info = fd.stat()
                if info.st_nlink != 0 or not stat.S_ISREG(info.st_mode): continue
            except FileNotFoundError: continue
            key = (info.st_dev, info.st_ino)
            if key not in seen:
                seen.add(key); total += max(info.st_size, info.st_blocks*512); count += 1
    need(total <= limits['own_stage_bytes'] and count <= limits['own_stage_inodes'],
         'Finite additive-stage storage bound exceeded')
    return {'bytes_including_child_unlinked': total, 'inodes': count,
            'cap_bytes': limits['own_stage_bytes'], 'cap_inodes': limits['own_stage_inodes']}


def main():
    p = load(SRC/'policy.json'); pin = source_check(SRC)
    need(str(SRC) == p['deployed_source'], 'Only reviewed deployed source may run this candidate')
    need(os.environ.get('PYTHONPATH') is None and os.environ.get('PYTHONHOME') is None
         and os.environ.get('PYTHONNOUSERSITE') == '1' and os.environ.get('PYTHONDONTWRITEBYTECODE') == '1',
         'Preserved Python isolation missing')
    need(Path(sys.executable).resolve() == Path(p['python']).resolve(), 'Unexpected Python executable')
    job = os.environ.get('SLURM_JOB_ID','')
    need(job.isdigit() and not os.environ.get('SLURM_ARRAY_JOB_ID'), 'Single actual allocation required')
    need(int(os.environ.get('SLURM_CPUS_PER_TASK','0')) == 2
         and int(os.environ.get('SLURM_MEM_PER_NODE','0')) == 16384, 'CPU/memory request differs from finite stage')
    controller = subprocess.run(['scontrol','show','job','-o',job], text=True, capture_output=True,
                                check=True, timeout=60).stdout
    c = dict(token.split('=',1) for token in controller.split() if '=' in token)
    tres = dict(item.split('=',1) for item in c.get('AllocTRES','').split(',') if '=' in item)
    need(c.get('JobId') == job and c.get('JobState') == 'RUNNING' and c.get('UserId') == 'mujahid(10796)'
         and c.get('Account') == 'molecular_neurosciences' and c.get('JobName') == 'p5-ATAC-res1'
         and c.get('NumNodes') == '1' and c.get('NumCPUs') == '2' and c.get('CPUs/Task') == '2'
         and tres.get('cpu') == '2' and MiB(tres.get('mem','')) == 16384
         and c.get('Requeue') == '0' and 0 < seconds(c.get('TimeLimit','')) <= 7200,
         'Actual RUNNING allocation owner/account/finite resources changed')
    base = Path(p['output_root']); base.mkdir(parents=True, exist_ok=True)
    out = base / ('job-'+job); out.mkdir(exist_ok=False); (out/'tmp').mkdir()
    child = None; lock = None; guard = None
    def interrupted(sig, frame): raise RuntimeError('Parent interrupted by signal '+str(sig))
    for sig in [signal.SIGTERM, signal.SIGINT]: signal.signal(sig, interrupted)
    try:
        source_check(Path(p['guard_source']), p['guard_source_manifest_sha256'])
        spec = importlib.util.spec_from_file_location('frozen_QC_guard', Path(p['guard_source'])/'guard.py')
        guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
        need(str(guard.ROOT) == p['project_root'], 'Pinned quota guard project root differs')
        need(p['storage']['shared_bytes'] == 500000000000 and p['storage']['shared_inodes'] == 40000
             and p['storage']['headroom_bytes'] == 605000000000 and p['storage']['headroom_inodes'] == 53000,
             'Storage admission/shared cap policy changed')
        guard.save(out/'quota_before.json', guard.quota()); first_usage = guard.usage(None)
        source_check(Path(p['accepted_source']), p['accepted_source_manifest_sha256'])
        need(sha(SRC/'frozen_marker_review.py') == p['marker_helper_sha256']
             and sha(SRC/'marker_panels.json') == p['marker_panels_sha256'], 'Copied marker helper/panels changed')
        for record in [p['atlas'], p['activity']]: input_check(record)
        lock = (base/'.stage.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        fd = os.open(base/'.run_once.intent.json', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as h:
            json.dump({'utc':guard.utc(),'job_id':job,'source_manifest_sha256':pin,
                       'accepted_atlas':p['atlas'],'resolution':1,'no_automatic_retry':True},h,indent=2)
            h.write('\n'); h.flush(); os.fsync(h.fileno())
        os.environ.update(TMPDIR=str(out/'tmp'), MPLCONFIGDIR=str(out/'tmp/mpl'), MPLBACKEND='Agg',
                          OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMBA_NUM_THREADS='2')
        guard.save(out/'started.json', {'utc':guard.utc(),'job_id':job,'controller':controller,
                   'source_manifest_sha256':pin,'inputs':[p['atlas'],p['activity']],
                   'explicit_Leiden_parameters':p['leiden'],'runtime_versions':p['runtime_versions'],
                   'shared_usage':first_usage,'raw_peak_X_will_not_be_read':True,
                   'new_marker_activity_counts_will_be_read_in_blocks':True,
                   'TFIDF_LSI_Harmony_UMAP_rerun':False,'initial_diagnostic_only':True})
        with (out/'science.log').open('w') as log:
            child = subprocess.Popen([sys.executable,'-B',str(SRC/'resolution1.py'),str(out)],
                        cwd=out,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            tick = 0.0
            while child.poll() is None:
                if time.monotonic() >= tick:
                    sample={'utc':guard.utc(),'quota':guard.quota(),'shared_usage':guard.usage(child),
                            'own_stage':own_usage(out,child,p['storage'])}
                    with (out/'storage_samples.jsonl').open('a') as h: h.write(json.dumps(sample)+'\n')
                    for record in [p['atlas'],p['activity']]: input_check(record)
                    tick=time.monotonic()+p['storage']['sample_seconds']
                time.sleep(1)
            need(child.wait()==0, 'Additive graph/marker child failed; inspect preserved science.log')
        need(load(out/'runtime_fixture/complete.json').get('status')=='passed', 'Required actual synthetic fixture missing')
        science = load(out/'science_complete.json')
        need(science.get('resolution')==1 and science.get('n_cells')==p['n_cells']
             and science.get('corrected_and_uncorrected_graphs_complete') is True
             and science.get('new_107_gene_activity_summaries_complete') is True
             and science.get('raw_peak_X_read') is False and science.get('source_atlas_modified') is False
             and science.get('TFIDF_LSI_Harmony_UMAP_rerun') is False,
             'Science completion lacks expected additive graph/marker scope')
        for record in [p['atlas'],p['activity']]: input_check(record)
        source_check(SRC,pin); source_check(Path(p['accepted_source']),p['accepted_source_manifest_sha256'])
        guard.save(out/'execution_complete.json',{'utc':guard.utc(),'job_id':job,'returncode':0,
             'science_complete_sha256':sha(out/'science_complete.json')})
        guard.save(out/'quota_after.json',guard.quota())
        guard.save(out/'storage_complete.json',{'utc':guard.utc(),'shared_usage':guard.usage(None),
             'own_stage':own_usage(out,None,p['storage'])})
        guard.save(out/'complete.json',{'utc':guard.utc(),'job_id':job,'returncode':0,'resolution':1,
             'source_manifest_sha256':pin,'n_cells':p['n_cells'],
             'corrected_and_uncorrected_saved_graph_clustering_complete':True,
             'new_107_gene_activity_markers_complete':True,'original_0_6_atlas_preserved':True,
             'TFIDF_LSI_Harmony_UMAP_rerun':False,'raw_peak_X_read':False,
             'final_cell_selection':False,'final_annotations_pending':True,'no_automatic_retry':True})
        own_usage(out,None,p['storage']); guard.usage(None); guard.quota()
    except BaseException as exc:
        terminate(child)
        record={'utc':guard.utc() if guard else None,'job_id':job,'error':repr(exc),
                'traceback':traceback.format_exc(),'partials_preserved':True,'no_automatic_retry':True}
        (out/'failed.json').write_text(json.dumps(record,indent=2)+'\n')
        raise
    finally:
        if lock is not None: lock.close()


if __name__=='__main__': main()
