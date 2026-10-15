import sys;sys.dont_write_bytecode=True
import pathlib,json,os,subprocess,hashlib,datetime,signal,traceback,fcntl
ROOT=pathlib.Path('/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging')
SRC=pathlib.Path('/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2')
job=os.environ['SLURM_JOB_ID'];assert job.isdigit()
assert int(os.environ['SLURM_CPUS_PER_TASK'])>=32 and int(os.environ['SLURM_MEM_PER_NODE'])>=131072
OUT=ROOT/'pre_processed_ATAC/analysis_runs/ATAC_embedding_20261014_v2'/('job-'+job)
OUT.mkdir(parents=True,exist_ok=False);receipt=OUT/'receipts/main';receipt.mkdir(parents=True)
tmp=OUT/'tmp';tmp.mkdir()
def save(n,v):(receipt/n).write_text(json.dumps(v,indent=2)+'\n')

def quota():
 r=subprocess.run(['/usr/lpp/mmfs/bin/mmlsquota','-Y','-u','mujahid','data'],capture_output=True,text=True,check=True);h=None;rows=[]
 for line in r.stdout.splitlines():
  p=line.split(':')
  if len(p)>2 and p[2]=='HEADER':h=p
  elif h:
   v=dict(zip(h,p))
   if v.get('id')=='10796' and v.get('filesetname')=='scratch':rows.append(v)
 assert len(rows)==1
 v=rows[0];available=(min(int(v['blockQuota']),int(v['blockLimit']))-int(v['blockUsage'])-int(v['blockInDoubt']))*1024
 inodes=min(int(v['filesQuota']),int(v['filesLimit']))-int(v['filesUsage'])-int(v['filesInDoubt'])
 # Single shared500GB allowance plus100GBreserve and5GBruntime; no completion/materialization credits.
 assert available>=605000000000 and inodes>=53000,('Combined RNA/ATAC scratch headroom insufficient',available,inodes,605000000000)
 return {'available_bytes':available,'available_inodes':inodes,'required_bytes':605000000000,'headroom_reserved':False,'raw':r.stdout}

child=None
for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda s,f:(_ for _ in ()).throw(RuntimeError('Stage terminated')))
def check_inputs():
 for f in json.loads((SRC/'input_identity_manifest.json').read_text()):
  p=pathlib.Path(f['path']);v=p.stat();assert not p.is_symlink() and (v.st_size,v.st_ino,v.st_mtime_ns)==(f['bytes'],f['inode'],f['mtime_ns']),str(p)
  if 'sha256' in f:assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],str(p)
try:
 controller=subprocess.check_output(['scontrol','show','job','-o',job],text=True)
 assert 'JobState=RUNNING' in controller and 'UserId=mujahid(10796)' in controller and 'Account=molecular_neurosciences' in controller
 for n,h in json.loads((SRC/'source_manifest.json').read_text()).items():assert hashlib.sha256((SRC/n).read_bytes()).hexdigest()==h,n
 check_inputs();save('quota_before.json',quota())
 lock=(ROOT/'pre_processed_ATAC/analysis_runs/ATAC_embedding_7462166.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 os.environ.update(P5_ATAC_JOB_OUTPUT=str(OUT),P5_ATAC_STAGE='embedding',TMPDIR=str(tmp),SQLITE_TMPDIR=str(tmp),MPLBACKEND='Agg',MPLCONFIGDIR=str(tmp/'matplotlib'),NUMBA_CACHE_DIR=str(tmp/'numba'),OMP_NUM_THREADS='32',OPENBLAS_NUM_THREADS='32',MKL_NUM_THREADS='32',NUMBA_NUM_THREADS='32',PYTHONDONTWRITEBYTECODE='1')
 argv=[sys.executable,'-B',str(SRC/'child_atlas.py'),'--receipt',str(receipt),'--',str(OUT)]
 save('started.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'job_id':job,'controller':controller,'argv':argv,'source_manifest_sha256':hashlib.sha256((SRC/'source_manifest.json').read_bytes()).hexdigest(),'aggregate_paths':[str(ROOT/'pre_processed_ATAC/analysis_runs'),str(ROOT/'pre_processed_RNA/analysis_runs')],'aggregate_cap_bytes':500000000000,'aggregate_file_cap':40000})
 with (receipt/'science.log').open('w') as log:
  child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  while True:
   try:rc=child.wait(timeout=30);break
   except subprocess.TimeoutExpired:quota()
 assert rc==0,('Scientific stage failed',rc)
 check_inputs();save('quota_after.json',quota());assert(receipt/'child_storage_complete.json').exists()
 c=json.loads((OUT/'embedding/initial_embedding_complete.json').read_text());assert c['n_initial_cells']==456472 and c['raw_counts_preserved'] and c['n_animals']==20 and not c['final_annotation_complete']
 assert json.loads((OUT/'marker_review/complete.json').read_text())['n_cells']==456472
 save('complete.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'job_id':job,'status':'complete_initial_ATAC_embedding_and_marker_diagnostics','final_retention_reviewed':False,'integration_complete':False})
except BaseException as e:
 if child and child.poll() is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 save('failed.json',{'error':repr(e),'traceback':traceback.format_exc(),'partial_products_preserved':True});raise
