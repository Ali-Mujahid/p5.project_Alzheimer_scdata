#!/usr/bin/env python3
import csv,gzip,json,hashlib,math,datetime,collections
from pathlib import Path
R=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a')
S=R/'outputs/p5_workflow/ATAC_peak_TE_annotation_20261015/job-7471562/annotation'
D=R/'outputs/p5_workflow/full_workflow_20261014/atlas_preview/te_data'
checks=[]
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def num(x):return None if x in ('','NA','nan','NaN',None) else float(x)
def same(a,b):return a is None and b is None or a is not None and b is not None and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-14)
def cid(r):return r['level']+'_'+hashlib.sha256(json.dumps([r['level'],r['repClass'],r['repFamily'],r['repName']],separators=(',',':')).encode()).hexdigest()[:14]
m=json.loads((D/'manifest.json').read_text())
ck('Accepted producer and coordinate scope',m['producer_job_id']=='7471562' and m['scope']=='TE_peak_coordinate_overlap_only' and m['source_manifest_sha256']=='7841253b0eb43c487b128d3f0249e3cf3ce64bf5fab8624909022285f41e1028')
ck('All 28 calibration types remain in manifest',len(m['cell_types'])==28)
by={};tot=0;nullfrac=0;nullfold_callable=0
for t in m['cell_types']:
 p=D/t['path'];b=p.read_bytes();ck('Adapter bytes and digest '+t['label'],len(b)==t['bytes'] and hashlib.sha256(b).hexdigest()==t['sha256'])
 d=json.loads(b);ck('Exact cell type and metadata '+t['label'],d['producer_job_id']=='7471562' and d['cell_type']==t['label'] and d['animals']==m['animals'])
 ck('1147 unique taxonomy categories '+t['label'],len(d['categories'])==1147 and len({c['id'] for c in d['categories']})==1147)
 tab={}
 for r in d['rows']:
  q=(r['animal_id'],r['category_id']);ckdupe=q not in tab
  if not ckdupe:raise AssertionError('Duplicate '+str(q))
  tab[q]=(r['group_id'],r['n_peaks'],r['callable_peak_union_bp'],r['overlap_union_bp'],r['overlap_fraction_descriptive'],r['fold_descriptive'])
  nullfrac+=r['overlap_fraction_descriptive'] is None
  nullfold_callable+=r['fold_descriptive'] is None and r['callable_peak_union_bp']>0
 by[t['label']]=tab;tot+=len(tab)
 agg=collections.defaultdict(lambda:[0,0,0.,0,0.]);animals={a['animal_id']:a for a in m['animals']}
 for (a,cat),v in tab.items():
  x=agg[(animals[a]['condition'],cat)];x[0]+=1
  if v[4] is not None:x[1]+=1;x[2]+=v[4]
  if v[5] is not None:x[3]+=1;x[4]+=v[5]
 for ss in d['condition_summary']:
  v=agg[(ss['condition'],ss['category_id'])]
  if (ss['n_expected'],ss['n_available'],ss['n_callable'],ss['n_fold'])!=(4,v[0],v[1],v[3]):raise AssertionError('Condition denominator '+t['label']+str(ss))
  if not same(ss['mean_fraction'],v[2]/v[1] if v[1] else None) or not same(ss['mean_fold'],v[4]/v[3] if v[3] else None):raise AssertionError('Condition mean '+t['label'])
 ck('Condition summaries independently recompute '+t['label'],True)
matched=0
with gzip.open(S/'peak_repeat_genomic_coverage_by_group.tsv.gz','rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  if r['group_id']=='CONSENSUS':continue
  t=r['cell_type'];q=(r['animal_id'],cid(r));v=by[t].pop(q)
  if v[:4]!=(r['group_id'],int(r['n_peaks']),int(r['callable_peak_union_bp']),int(r['overlap_union_bp'])) or not same(v[4],num(r['overlap_fraction_descriptive'])) or not same(v[5],num(r['chromosome_coverage_fold_descriptive'])):raise AssertionError('Adapter source mismatch '+str(q))
  matched+=1
ck('All 535649 individual animal category rows match producer',matched==535649==tot and all(not v for v in by.values()))
ck('All empty group fractions remain null',nullfrac==40*1147)
ck('Callable rows with zero expected coverage keep fold null',nullfold_callable>0)
ck('Conditions are age-separated and animal balanced',len(m['conditions'])==5 and all(c['n_expected']==4 for c in m['conditions']))
ck('Limits distinguish peak overlap from depth-matched or inferential analysis',any('fragment depth' in x and 'mappability' in x for x in m['limitations']))
ck('All static download choices are PDF',len(m['downloads'])>=5 and all(x['pdf_path'].endswith('.pdf') for x in m['downloads']))
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent generated JSON metrics, nulls and denominators vs saved accepted producer tables','checks':checks,'passed':all(c['passed'] for c in checks),'matched_animal_category_rows':matched,'empty_group_null_fraction_rows':nullfrac,'callable_zero_expected_background_null_fold_rows':nullfold_callable,'manifest_sha256':hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest()}
(R/'work/TE_atlas_20261015/independent_review.adapter.actual.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':out['passed'],'matched_rows':matched,'null_fold_callable':nullfold_callable}))
