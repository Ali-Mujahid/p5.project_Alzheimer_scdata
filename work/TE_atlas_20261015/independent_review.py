#!/usr/bin/env python3
"""Independent review of saved, accepted small group tables; no peak/matrix rescan."""
import csv,gzip,json,hashlib,math,statistics,collections,datetime
from pathlib import Path
ROOT=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a')
P=ROOT/'outputs/p5_workflow/ATAC_peak_TE_annotation_20261015/job-7471562'
A=P/'annotation'
OUT=ROOT/'work/TE_atlas_20261015'
checks=[]
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def rs(n):
 with (gzip.open(A/n,'rt') if n.endswith('.gz') else open(A/n)) as f:return list(csv.DictReader(f,delimiter='\t'))
def num(x):return None if x in ('','NA','nan','NaN') else float(x)
def cat(r):return '|'.join([r['repClass'],r['repFamily'],r['repName']])
def key(r):return(r['group_id'],r['level'],cat(r))
manifest=json.loads((P/'download_manifest.actual.json').read_text())
names=['available_animal_type_groups.tsv','group_coverage_summary.tsv','peak_repeat_genomic_coverage_by_group.tsv.gz','equal_animal_calibration_type_repeat_coverage.tsv.gz','microglia_all_repeat_coverage_animal_details.tsv.gz','reference_taxonomy_rows.tsv','coordinate_complete.json']
for n in names:
 b=(A/n).read_bytes();r=manifest['files']['annotation/'+n]
 check('download local digest '+n,len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['local_content_sha256'])
av=rs(names[0]);gg=rs(names[1]);eq=rs(names[3]);micro=rs(names[4]);tax=rs(names[5])
groups={r['group_id']:r for r in gg};availability={(r['cell_type'],r['animal_id']):r for r in av}
check('467 unique available animal type groups',len(av)==len(availability)==467)
check('468 unique group summaries including consensus',len(gg)==len(groups)==468 and 'CONSENSUS' in groups)
check('28 calibration types',len({r['cell_type'] for r in av})==28)
check('all available animal type groups have a summary',set(availability)=={(r['cell_type'],r['animal_id']) for r in gg if r['group_id']!='CONSENSUS'})
animals={}
for r in av:
 ident={k:r[k] for k in ['animal_id','condition','genotype','age','sex','replicate']}
 if r['animal_id'] in animals:check('consistent metadata '+r['animal_id'],animals[r['animal_id']]==ident)
 animals[r['animal_id']]=ident
check('20 biological animals',len(animals)==20)
conditions=['WT_3mo','5xFAD_3mo','APOE4_TREM2_3mo','WT_6mo','WT_21mo']
check('five age genotype conditions',set(r['condition'] for r in animals.values())==set(conditions))
for condition in conditions:
 aa=[r for r in animals.values() if r['condition']==condition]
 check('four animals and two of each sex '+condition,len(aa)==4 and collections.Counter(r['sex'] for r in aa)=={'female':2,'male':2})
empty={g for g,r in groups.items() if r['empty_or_noncallable']=='True'}
check('40 empty/noncallable groups',len(empty)==40)
check('empty groups have zero callable bases and peaks',all(int(groups[g]['callable_peak_union_bp'])==0 and int(groups[g]['n_peaks'])==0 for g in empty))
primary=sorted({r['repClass'] for r in tax if r['repeat_kind']=='TE_primary'})
check('native primary class set',primary==['DNA','LINE','LTR','RC','SINE'])
agg=collections.defaultdict(lambda:[0,0.0,0,0.0]);counts=collections.Counter();levels=collections.defaultdict(set);microcheck={key(r):r for r in micro};main_micro={};row_count=0;zero_callable_rows=0
with gzip.open(A/names[2],'rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  row_count+=1;g=r['group_id'];den=int(r['callable_peak_union_bp']);ov=int(r['overlap_union_bp']);frac=num(r['overlap_fraction_descriptive']);fold=num(r['chromosome_coverage_fold_descriptive']);ex=num(r['chromosome_weighted_expected_bp']);counts[g]+=1;levels[r['level']].add(cat(r))
  if den==0:
   zero_callable_rows+=1
   if frac is not None or fold is not None or ov!=0:raise AssertionError('empty NA semantics '+str(key(r)))
  else:
   if not (0<=ov<=den and frac is not None and math.isclose(frac,ov/den,abs_tol=1e-14)):raise AssertionError('fraction '+str(key(r)))
   if ex is not None and ex>0 and not math.isclose(fold,ov/ex,rel_tol=1e-12,abs_tol=1e-14):raise AssertionError('fold '+str(key(r)))
  if any(r[k]!=groups[g][k] for k in ['cell_type','animal_id','genotype','age','sex','replicate','n_peaks','raw_peak_union_bp','callable_peak_union_bp']):raise AssertionError('group join '+g)
  if g!='CONSENSUS' and frac is not None:
   v=agg[(r['cell_type'],r['level'],cat(r))];v[0]+=1;v[1]+=frac
   if fold is not None:v[2]+=1;v[3]+=fold
  if r['cell_type']=='Microglia':main_micro[key(r)]=r
check('536796 coverage rows exact group category grid',row_count==536796 and set(counts.values())=={1147})
check('all 45880 empty rows use NA fractions/folds',zero_callable_rows==40*1147)
def same_value(a,b):
 if a==b:return True
 try:
  aa=num(a);bb=num(b)
  return aa is not None and bb is not None and math.isclose(aa,bb,rel_tol=1e-12,abs_tol=1e-14)
 except ValueError:return False
check('microglia extract source values agree within serialized float tolerance',len(main_micro)==len(microcheck)==22940 and all(all(same_value(v[k],microcheck[q][k]) for k in v) for q,v in main_micro.items()))
for r in eq:
 k=(r['cell_type'],r['level'],r['category']);v=agg[k];frac=num(r['equal_animal_mean_fraction']);fold=num(r['equal_animal_mean_descriptive_fold'])
 if int(r['n_callable_animals'])!=v[0] or int(r['n_animals_available'])!=sum(a['cell_type']==r['cell_type'] for a in av):raise AssertionError('animal denominator '+str(k))
 if v[0] and not math.isclose(frac,v[1]/v[0],abs_tol=1e-13):raise AssertionError('equal animal fraction '+str(k))
 if v[2] and not math.isclose(fold,v[3]/v[2],abs_tol=1e-13):raise AssertionError('equal animal fold '+str(k))
 if not v[2] and fold is not None:raise AssertionError('no finite fold '+str(k))
check('all32116 saved equal animal categories independently reproduce',len(eq)==28*1147)
summary={}
for level,classes in [('any_primary_TE',['ALL']),('class',primary)]:
 for cl in classes:
  by={}
  for co in conditions:
   rr=[r for r in micro if r['level']==level and r['repClass']==cl and r['condition']==co]
   check('microglia four callable animals '+level+cl+co,len(rr)==4 and all(int(r['callable_peak_union_bp'])>0 for r in rr))
   vs=[float(r['overlap_fraction_descriptive'])*100 for r in rr];fs=[float(r['chromosome_coverage_fold_descriptive']) for r in rr]
   by[co]={'n_animals':len(rr),'mean_peak_bp_coverage_percent':statistics.mean(vs),'min_percent':min(vs),'max_percent':max(vs),'mean_descriptive_genomic_fold':statistics.mean(fs),'animals':[{'animal_id':r['animal_id'],'sex':r['sex'],'n_peaks':int(r['n_peaks']),'callable_peak_union_bp':int(r['callable_peak_union_bp']),'overlap_union_bp':int(r['overlap_union_bp']),'percent':float(r['overlap_fraction_descriptive'])*100,'descriptive_genomic_fold':float(r['chromosome_coverage_fold_descriptive'])} for r in rr]}
  summary[level+':'+cl]=by
rc_nonzero=[{'animal_id':r['animal_id'],'overlap_union_bp':int(r['overlap_union_bp']),'descriptive_genomic_fold':float(r['chromosome_coverage_fold_descriptive'])} for r in micro if r['level']=='class' and r['repClass']=='RC' and int(r['overlap_union_bp'])>0]
type_coverage=[{'cell_type':t,'n_available_animals':sum(r['cell_type']==t for r in av),'n_callable_animals':sum(r['cell_type']==t and r['empty_or_noncallable']=='False' for r in gg)} for t in sorted({r['cell_type'] for r in av})]
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent saved-group table validation only; no original peak/matrix/BAM read','producer_job_id':'7471562','checks':checks,'passed':all(r['passed'] for r in checks),'available_groups':467,'callable_groups':427,'empty_groups':40,'absent_animal_type_combinations':28*20-467,'cell_types':28,'animals':list(animals.values()),'coverage_rows':row_count,'native_primary_classes':primary,'native_primary_families':len({(r['repClass'],r['repFamily']) for r in tax if r['repeat_kind']=='TE_primary'}),'native_primary_subfamilies':sum(r['repeat_kind']=='TE_primary' for r in tax),'type_callable_coverage':type_coverage,'microglia':summary,'microglia_RC_nonzero_animals':rc_nonzero,'interpretation_limits':['Calibration types are initial published-seed peak groups, not final independent labels.','Overlap fraction is category-union bp divided by callable peak-union bp, not fraction of nuclei or reads.','Classes/families/subfamilies can overlap; category fractions need not sum to 100%.','Genome coverage fold is descriptive chromosome weighted background, unmatched for GC, TSS/gene context or mappability.','No disease effect test, p-value or FDR; animal points are the biological units.','Genotype comparisons are age matched at 3mo; WT6mo and WT21mo remain separate aging conditions.','Peak calls and widths differ by animal, with no fragment-depth or peak-number matched inference.','No TE expression, TE fragment accessibility quantification, or final retention certification.','Zero callable or absent groups are unavailable/NA; callable no-overlap categories are true zero.']}
(OUT/'independent_review.actual.json').write_text(json.dumps(out,indent=2)+'\n')
(OUT/'independent_review.md').write_text('''# Independent review of TE overlap genotype atlas data\n\nVerified job 7471562 saved group tables and download digests. All '''+str(len(checks))+''' checks passed. No raw peaks, cell matrices or BAMs were reread.\n\n- All 28 initial calibration types remain represented. There are 467 available animal × type groups, of which 427 are callable and 40 have no callable peaks. A further 93 type × animal combinations were not available. Empty and absent groups must display as NA.\n- All 20 microglia groups are callable. Each age–genotype condition has four animals, two female and two male.\n- In microglia, any primary TE overlap covers a mean 5.7434% of callable peak bases in WT 3mo, 6.4630% in 5xFAD 3mo and 6.6265% in APOE4_TREM2 3mo. Respective descriptive genome-coverage folds are 0.1470, 0.1655 and 0.1697: all are below one. These descriptive differences are not a tested genotype effect.\n- LTR is the largest microglia class by peak-base overlap in all five conditions. Its 3mo mean is 2.3601%, 2.4531% and 2.5979% for WT, 5xFAD and APOE4_TREM2. Native primary classes are DNA, LINE, LTR, RC and SINE; uncertain and non-TE repeat classes remain separate. Native repFamily is the family/subclass alias; repName is subfamily.\n- RC coverage-fold rankings are sparse and animal driven. APOE4_TREM2 female R2 alone has 109 overlapping bp and fold 3.188, while the other three APOE4_TREM2 animals have zero. It must not be presented as a consistent enrichment.\n- Microglia peak counts range from 4,829 to 11,679 across animals. Peak-call discovery, widths and sequencing depth are not matched by these overlap summaries.\n\nAll 32,116 saved equal-animal category summaries reproduce from 536,796 source coverage rows. No TE expression, fragment-level TE accessibility, final cell identities or differential inference is established.\n''')
print(json.dumps({'checks':len(checks),'passed':out['passed'],'out':str(OUT/'independent_review.actual.json')}))
