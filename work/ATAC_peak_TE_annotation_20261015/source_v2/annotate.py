"""All-hit mm10 RepeatMasker coordinate annotation; descriptive coverage only."""
import sys
sys.dont_write_bytecode = True
import bisect
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
from common import IntervalIndex

TE_CLASSES = frozenset({'DNA','LINE','LTR','RC','Retroposon','SINE'})
NON_TE = frozenset({'Simple_repeat','Low_complexity','Satellite','snRNA','srpRNA','tRNA','RNA','scRNA','rRNA'})
LONG_FIELDS = ['peak_id','chrom','peak_start','peak_end','rmsk_row_id','rmsk_source_id','repeat_start','repeat_end','repeat_strand','repClass','repFamily','repName','repeat_kind','raw_overlap_bp','callable_overlap_bp']
EXTRA_FIELDS = ['annotation_peak_id','peak_width_bp','peak_callable_bp','blacklist_overlap_bp','n_rmsk_hits','native_repClass_json','native_class_family_pairs_json','native_class_family_subfamily_triples_json','user_subclass_definition','TE_primary_callable_union_bp','non_TE_repeat_callable_union_bp','uncertain_or_unclassified_repeat_callable_union_bp']


def need(ok,message):
    if not ok: raise RuntimeError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def kind(label):
    if label in TE_CLASSES:return 'TE_primary'
    if label in NON_TE:return 'non_TE_repeat'
    if label.rstrip('?') in TE_CLASSES:return 'uncertain_TE_class'
    return 'unclassified_repeat'


def merge(intervals):
    out=[]
    for a,b in sorted(intervals):
        need(0<=a<b,'Invalid union interval')
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
        else:out.append((a,b))
    return out


def length(intervals):return sum(b-a for a,b in merge(intervals))


class Masks:
    def __init__(self,values):
        self.by_chr={c:merge(v) for c,v in values.items()}
        self.ends={c:[b for a,b in v] for c,v in self.by_chr.items()}
    def callable(self,chrom,a,b):
        out=[];cursor=a;v=self.by_chr.get(chrom,[])
        i=bisect.bisect_right(self.ends.get(chrom,[]),a)
        while i<len(v) and v[i][0]<b:
            left,right=v[i]
            if cursor<left:out.append((cursor,min(b,left)))
            cursor=max(cursor,right)
            if cursor>=b:break
            i+=1
        if cursor<b:out.append((cursor,b))
        return out


def categories(teclass,family,name):
    # Native labels remain tuples: ambiguous subfamily/family relations are not collapsed.
    ans=[('any_repeat','ALL','ALL','ALL'),('class',teclass,'','')]
    if teclass in TE_CLASSES:
        ans.extend([('any_primary_TE','ALL','ALL','ALL'),('family',teclass,family,''),('subfamily',teclass,family,name)])
    return ans


def load_reference(rmsk_path,sizes_path,blacklist_path):
    sizes={}
    for line in Path(sizes_path).read_text().splitlines():
        c,n=line.split()[:2]
        if re.fullmatch(r'chr(?:[1-9]|1[0-9]|X|Y)',c):
            need(c not in sizes and int(n)>0,'Invalid/duplicate nuclear chromosome');sizes[c]=int(n)
    need(set(sizes)=={f'chr{i}' for i in range(1,20)}|{'chrX','chrY'},'Require canonical mm10 nuclear chromosome set')
    excluded=collections.Counter(); masks=collections.defaultdict(list)
    for line in Path(blacklist_path).read_text().splitlines():
        if not line or line.startswith('#'):continue
        cols=line.split();c=cols[0];a,b=map(int,cols[1:3])
        if c not in sizes:excluded['blacklist_non_nuclear_rows']+=1;continue
        need(0<=a<b<=sizes[c],'Blacklist coordinate bounds');masks[c].append((a,b))
    masks=Masks(masks); intervals=[]; genome=collections.defaultdict(lambda:collections.defaultdict(list))
    taxonomy=collections.Counter()
    with Path(rmsk_path).open() as f:
        for number,line in enumerate(f,1):
            if not line.strip() or line.startswith('#'):continue
            r=line.rstrip('\n').split('\t');need(len(r)==17,'Require exact17column UCSC rmsk including bin')
            c=r[5];a,b=int(r[6]),int(r[7])
            if c not in sizes:excluded['rmsk_non_nuclear_rows']+=1;continue
            need(0<=a<b<=sizes[c] and r[9] in ['+','-'] and all(r[x] for x in [10,11,12]),'Invalid RMSK coordinate/taxonomy')
            name,cl,fam=(sys.intern(r[x]) for x in [10,11,12]);payload=(number,r[16],r[9],cl,fam,name)
            intervals.append((c,a,b,payload));taxonomy[(cl,fam,name,kind(cl))]+=1
            for cat in categories(cl,fam,name):genome[cat][c].append((a,b))
    need(intervals,'Empty nuclear RepeatMasker reference')
    background={}
    for cat,by_chr in genome.items():
        background[cat]={c:sum(y-x for a,b in merge(v) for x,y in masks.callable(c,a,b)) for c,v in by_chr.items()}
    callable_sizes={c:sum(b-a for a,b in masks.callable(c,0,n)) for c,n in sizes.items()}
    need(all(n>0 for n in callable_sizes.values()),'No callable chromosome bases')
    return IntervalIndex(intervals),masks,sizes,callable_sizes,background,taxonomy,excluded


def read_peaks(path,fmt,sizes,expected_group=None):
    seen=set()
    if fmt=='consensus':
        with Path(path).open() as f:
            reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames
            need(fields and {'feature_id','chrom','start','end','assembly'}.issubset(fields),'Accepted consensus schema differs')
            rows=list(reader)
        def normalized(r):
            need(r['assembly']=='mm10','Consensus assembly differs');return r['feature_id'],r['chrom'],int(r['start']),int(r['end'])
    else:
        fields=['chrom','start','end','name','score','strand','signalValue','pValue','qValue','peak']
        rows=[]
        with Path(path).open() as f:
            for line in f:
                if not line.strip():continue
                r=line.rstrip('\n').split('\t');need(len(r)==10,'MACS narrowPeak must have10columns');rows.append(dict(zip(fields,r)))
        def normalized(r):return r['name'],r['chrom'],int(r['start']),int(r['end'])
    need(not set(fields).intersection(EXTRA_FIELDS),'Annotated columns would overwrite producer columns')
    peaks=[]
    for row in rows:
        pid,c,a,b=normalized(row);need(pid and pid not in seen,'Duplicate/empty peak identifier');seen.add(pid)
        if expected_group is not None:need(re.fullmatch(re.escape(expected_group)+r'_peak_[0-9]+[a-z]*',pid) is not None,'MACS peak name/group association differs')
        need(c in sizes and 0<=a<b<=sizes[c],'Peak outside canonical nuclear mm10 ranges')
        peaks.append((row,pid,c,a,b))
    return fields,peaks


def summarize_group(peaks,index,masks,callable_sizes,background,summary_path,hits_path,fields):
    by_chr=collections.defaultdict(list);covered=collections.defaultdict(lambda:collections.defaultdict(list))
    hit_count=0
    with gzip.open(summary_path,'wt',compresslevel=3) as sf,gzip.open(hits_path,'wt',compresslevel=3) as hf:
        sw=csv.DictWriter(sf,fieldnames=fields+EXTRA_FIELDS,delimiter='\t',lineterminator='\n');sw.writeheader()
        hw=csv.DictWriter(hf,fieldnames=LONG_FIELDS,delimiter='\t',lineterminator='\n');hw.writeheader()
        for original,pid,c,a,b in peaks:
            by_chr[c].append((a,b));hits=index.overlap(c,a,b);perkind=collections.defaultdict(list)
            labels=set();pairs=set();triples=set()
            for left,right,(rowid,sourceid,strand,cl,fam,name) in sorted(hits,key=lambda v:(v[0],v[1],v[2][0])):
                lo,hi=max(a,left),min(b,right);segments=masks.callable(c,lo,hi);callable_bp=sum(y-x for x,y in segments)
                labels.add(cl);pairs.add((cl,fam));triples.add((cl,fam,name));perkind[kind(cl)].extend(segments)
                for cat in categories(cl,fam,name):covered[cat][c].extend(segments)
                hw.writerow(dict(peak_id=pid,chrom=c,peak_start=a,peak_end=b,rmsk_row_id=rowid,rmsk_source_id=sourceid,
                    repeat_start=left,repeat_end=right,repeat_strand=strand,repClass=cl,repFamily=fam,repName=name,
                    repeat_kind=kind(cl),raw_overlap_bp=hi-lo,callable_overlap_bp=callable_bp));hit_count+=1
            callable_bp=sum(y-x for x,y in masks.callable(c,a,b))
            extra=dict(annotation_peak_id=pid,peak_width_bp=b-a,peak_callable_bp=callable_bp,blacklist_overlap_bp=b-a-callable_bp,
                n_rmsk_hits=len(hits),native_repClass_json=json.dumps(sorted(labels)),native_class_family_pairs_json=json.dumps(sorted(pairs)),
                native_class_family_subfamily_triples_json=json.dumps(sorted(triples)),user_subclass_definition='native repFamily alias; not a new taxonomic rank',
                TE_primary_callable_union_bp=length(perkind['TE_primary']),non_TE_repeat_callable_union_bp=length(perkind['non_TE_repeat']),
                uncertain_or_unclassified_repeat_callable_union_bp=length(perkind['uncertain_TE_class']+perkind['unclassified_repeat']))
            sw.writerow(dict(original,**extra))
    peak_callable_by_chr={c:sum(y-x for a,b in merge(v) for x,y in masks.callable(c,a,b)) for c,v in by_chr.items()}
    denominator=sum(peak_callable_by_chr.values());raw_bp=sum(length(v) for v in by_chr.values());rows=[]
    for cat,bg in sorted(background.items()):
        observed=sum(length(v) for v in covered.get(cat,{}).values())
        expected=sum(n*bg.get(c,0)/callable_sizes[c] for c,n in peak_callable_by_chr.items())
        need(0<=observed<=denominator,'Union overlap exceeds callable peak universe')
        rows.append(dict(level=cat[0],repClass=cat[1],repFamily=cat[2],repName=cat[3],repeat_kind=kind(cat[1]) if cat[0] not in ['any_repeat','any_primary_TE'] else cat[0],
            n_peaks=len(peaks),raw_peak_union_bp=raw_bp,callable_peak_union_bp=denominator,overlap_union_bp=observed,
            overlap_fraction_descriptive=(observed/denominator if denominator else None),
            chromosome_weighted_expected_bp=(expected if denominator else None),
            chromosome_weighted_expected_fraction=(expected/denominator if denominator else None),
            chromosome_coverage_fold_descriptive=(observed/expected if denominator and expected>0 else None)))
    return rows,dict(n_peaks=len(peaks),raw_peak_union_bp=raw_bp,callable_peak_union_bp=denominator,rmsk_hits=hit_count,
                     empty_or_noncallable=(denominator==0))


def verify_input(record):
    path=Path(record['path']);s=path.stat()
    need((s.st_size,s.st_ino,s.st_mtime_ns)==(record['bytes'],record['inode'],record['mtime_ns']),'Accepted input identity differs: '+str(path))
    if record.get('allowed_resolved_root'):
        path.resolve(strict=True).relative_to(Path(record['allowed_resolved_root']))
    else:need(not path.is_symlink(),'Reference/input unexpectedly became a symlink')
    digest=sha(path)
    if record.get('sha256'):need(digest==record['sha256'],'Producer/reference SHA differs: '+str(path))
    return dict(record,observed_SHA256=digest,digest_origin=('pinned producer/reference checksum' if record.get('sha256') else 'fresh allocation hash of identity-verified accepted consensus'))


def validate_catalog(catalog):
    need(catalog['assembly']=='mm10','Explicit mm10 catalog required')
    groups=catalog['groups']
    need(len(groups)==467 and len({r['group_id'] for r in groups})==467,'Exact467unique producer groups required')
    need(len({(r['animal_id'],r['cell_type']) for r in groups})==467,'Duplicate animal/calibration-type route')
    slugs=[r['descriptive_name'] for r in groups]
    need(all(re.fullmatch('[A-Za-z0-9_]+',v) for v in slugs) and len({v.casefold() for v in slugs})==467,
         'Descriptive outputs could collide or escape destination')
    with Path(catalog['groups_table']['path']).open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
    need(len(rows)==467 and len({r['group_id'] for r in rows})==467,'Producer group table is not467unique rows')
    by={r['group_id']:r for r in rows}
    need(set(by)=={r['group_id'] for r in groups},'Catalog groups differ from producer table')
    atlas=Path(catalog['groups_table']['path']).parent
    for r in groups:
        original=by[r['group_id']]
        need((original['animal_id'],original['cell_type'])==(r['animal_id'],r['cell_type']),
             'Catalog animal/calibration label differs from producer group')
        match=re.fullmatch(r'(.+)_(\d+mo)_(female|male)_([12])',r['animal_id'])
        need(match is not None,'Invalid accepted biological animal identifier')
        genotype,age,sex,rep=match.groups()
        need((r['genotype'],r['age'],r['sex'],r['replicate'])==(genotype,age,sex,'R'+rep),
             'Genotype/age/sex/biological replicate metadata changed')
        need(Path(r['input']['path'])==atlas/'peak_calls'/r['group_id']/(r['group_id']+'_peaks.narrowPeak') and
             Path(r['input']['allowed_resolved_root'])==atlas/'peak_calls','Producer group/peak path association changed')
    need(len({r['animal_id'] for r in groups})==20,'Accepted20animal peak discovery design differs')


def main(catalog_path,out):
    catalog=json.loads(Path(catalog_path).read_text());validate_catalog(catalog)
    admitted=[verify_input(r) for r in catalog['references'].values()]
    admitted.extend(verify_input(catalog[n]) for n in ['groups_table','producer_complete','consensus'])
    out.mkdir(exist_ok=False);(out/'annotated_peaks').mkdir();(out/'peak_repeat_hits').mkdir()
    index,masks,sizes,callable_sizes,background,taxonomy,excluded=load_reference(*[catalog['references'][n]['path'] for n in ['rmsk','chrom_sizes','blacklist']])
    fields=['group_id','cell_type','animal_id','genotype','age','sex','replicate','level','repClass','repFamily','repName','repeat_kind',
            'n_peaks','raw_peak_union_bp','callable_peak_union_bp','overlap_union_bp','overlap_fraction_descriptive','chromosome_weighted_expected_bp','chromosome_weighted_expected_fraction','chromosome_coverage_fold_descriptive']
    group_summary=[]
    with gzip.open(out/'peak_repeat_genomic_coverage_by_group.tsv.gz','wt',compresslevel=3) as af:
        writer=csv.DictWriter(af,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writeheader()
        sources=[dict(group_id='CONSENSUS',cell_type='common_consensus_all_calibration_types',animal_id='',genotype='',age='',sex='',replicate='',descriptive_name='common_consensus_mm10',input=catalog['consensus']),*catalog['groups']]
        for source in sources:
            rec=source['input'];check=verify_input(rec);admitted.append(check)
            cols,peaks=read_peaks(rec['path'],'consensus' if source['group_id']=='CONSENSUS' else 'narrowPeak',sizes,None if source['group_id']=='CONSENSUS' else source['group_id'])
            if source['group_id']=='CONSENSUS':need(len(peaks)==68126,'Accepted common68126peak universe differs')
            slug=source['descriptive_name'];need(re.fullmatch('[A-Za-z0-9_]+',slug),'Unsafe descriptive output name')
            rows,summary=summarize_group(peaks,index,masks,callable_sizes,background,out/'annotated_peaks'/(slug+'.annotated.tsv.gz'),out/'peak_repeat_hits'/(slug+'.rmsk_hits.tsv.gz'),cols)
            meta={k:source[k] for k in fields[:7]}
            for row in rows:writer.writerow(dict(meta,**row))
            group_summary.append(dict(meta,**summary));need(verify_input(rec)['observed_SHA256']==check['observed_SHA256'],'Peak input changed during annotation')
    with (out/'group_coverage_summary.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(group_summary[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(group_summary)
    for record in admitted:need(verify_input(record)['observed_SHA256']==record['observed_SHA256'],'Input changed before coordinate completion')
    (out/'input_checksums.actual.json').write_text(json.dumps(admitted,indent=2)+'\n')
    (out/'reference_taxonomy_rows.tsv').write_text('repClass\trepFamily\trepName\trepeat_kind\tn_source_rows\n'+''.join('\t'.join(map(str,(*key,n)))+'\n' for key,n in sorted(taxonomy.items())))
    result=dict(status='coordinate_annotation_complete_descriptive_coverage_only',assembly='mm10',peak_groups=467,common_consensus_peaks=68126,
      all_repeat_overlaps_preserved=True,subclass_definition='native repFamily alias; no invented taxonomy',
      genomic_background='per-chromosome union repeat coverage over blacklist-excluded canonical nuclear bases; weighted by each group callable peak-union bp',
      background_unmatched_covariates=['GC','TSS/gene context','mappability'],inferential_enrichment=False,p_values_or_FDR=False,
      TE_expression_measured=False,TE_fragment_accessibility_measured=False,raw_matrix_read=False,final_cell_types_assigned=False,
      labels='producer published calibration cell types only; rare/novel final labels and refined peaks remain pending',
      category_denominators='union bp within each category; categories may overlap so sums across classes/families/subfamilies can exceed100%; one peak can occur in multiple categories',
      empty_groups='preserved with NA fractions/folds, not fabricated zero coverage',excluded_reference_rows=dict(excluded),normalization_ready=False)
    (out/'coordinate_complete.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
