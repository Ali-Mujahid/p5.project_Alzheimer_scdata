#!/usr/bin/env python3
"""All-candidate mouse ATAC fragments and first-pass mm10 QC after mapping.

One task per PCR pool; technical BAM partitions share one coordinate-key DB.
Published cells/labels are calibration annotations, never a candidate whitelist.
Source queryname BAMs, including all secondary placements, remain untouched.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

CANONICAL = [f'chr{i}' for i in range(1,20)] + ['chrX','chrY']
REASONS = ['unmapped_or_mate_unmapped','vendor_qc_failed','not_exactly_two_primary_mates',
           'multimapping','supplementary_or_chimeric','improper_or_unpaired','invalid_mate_flags',
           'discordant_chromosomes','mitochondrial','excluded_chromosome','low_mapq',
           'unexpected_spliced_atac_alignment','blacklist_overlap']
COORDINATES = '0-based half-open genomic outer alignment span, no Tn5 shifting'
POLICY = 'all observed mapped barcodes with validated LIG10 and donor-linked N5+N7; published whitelist is calibration only'
DEFAULT_PROJECT = Path('/gpfs/data/fs72079/MujahidAli/p5_Glial_TE_regulation_aging')


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


def table(path):
    with (gzip.open(path,'rt') if str(path).endswith('.gz') else open(path)) as f:
        yield from csv.DictReader(f,delimiter='\t')


def write_table(path,fields,rows):
    with (gzip.open(path,'wt') if str(path).endswith('.gz') else open(path,'w')) as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)


def new_json(path,value):
    with open(path,'x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')


def bam_identity(path):
    s=Path(path).stat()
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def modules(project):
    # Reuse the established exact eligibility/CIGAR/blacklist algorithm unchanged.
    te=project/'workflow/te'
    if not te.is_dir():te=Path(__file__).resolve().parents[1]/'te'
    sys.path.insert(0,str(te))
    import atac_fragments
    return atac_fragments, {name:sha(te/name) for name in ('atac_fragments.py','count_rna.py','common.py')}


def pools(catalog):
    grouped=defaultdict(list)
    for row in table(catalog):
        if row['assay']=='ATAC':
            if not re.fullmatch(r'SRR\d+',row['run']) or not row['pool'] or int(row['bytes'])<=0:
                raise ValueError('Invalid completed ATAC mapping row')
            grouped[row['pool']].append(row)
    if not grouped:raise ValueError('No complete ATAC BAMs in catalog')
    return [(p,grouped[p]) for p in sorted(grouped)]


def donor_lookup(path):
    result={};by_donor={}
    for row in table(path):
        bc=row['tn5_barcode12']
        if not re.fullmatch('[ACGT]{12}',bc) or bc!=row['tn5_n5_barcode6']+row['tn5_n7_barcode6'] or bc in result:
            raise ValueError('Invalid/duplicate exact N5+N7 donor barcode')
        fields={k:row[k] for k in ('donor_id','condition','age_months','sex','replicate')}
        if fields['donor_id'] in by_donor and by_donor[fields['donor_id']]!=fields:
            raise ValueError('Conflicting biological donor metadata')
        by_donor[fields['donor_id']]=fields;result[bc]=fields
    if len(result)!=384 or len(by_donor)!=20:raise ValueError('Expected384 Tn5 barcodes and20 animals')
    return result


def ligation_lookup(path):
    values={line.strip().split()[0] for line in open(path) if line.strip()}
    if len(values)!=384 or any(not re.fullmatch('[ACGT]{10}',x) for x in values):
        raise ValueError('Expected384 exact EasySci ATAC ligation barcodes')
    return values


def published_lookup(path,pool):
    result={}
    for row in table(path):
        if row['library_id']==pool:
            if row['cell_id'] in result:raise ValueError('Duplicate published cell ID')
            result[row['cell_id']]=row
    return result


def read_reference(contract):
    ref=json.loads(Path(contract).read_text())
    if ref.get('genome')!='GRCm38/mm10' or ref.get('gene_release')!='GENCODE M25':
        raise ValueError('mm10/GRCm38 with GENCODE M25 reference required')
    sizes={}
    for line in open(ref['files']['chrom_sizes']['path']):
        chrom,length=line.split()[:2]
        if chrom in sizes or int(length)<=0:raise ValueError('Invalid chromosome sizes')
        sizes[chrom]=int(length)
    if not set(CANONICAL+['chrM'])<=set(sizes):raise ValueError('Incomplete canonical mm10 sizes')
    for key in ('chrom_sizes','blacklist'):
        if sha(ref['files'][key]['path'])!=ref['files'][key]['sha256']:raise ValueError('Reference hash mismatch:'+key)
    return ref,sizes


def transcript_tss(path,sizes):
    # Exact transcript-TSS definition and +/-2000 boundary policy used by build_mm10_atac.py.
    tss=defaultdict(set)
    with (gzip.open(path,'rt') if str(path).endswith('.gz') else open(path)) as f:
        for line in f:
            if line.startswith('#') or not line.strip():continue
            fields=line.rstrip().split('\t')
            if len(fields)!=9:raise ValueError('Malformed GTF')
            if fields[0] not in CANONICAL or fields[2]!='transcript':continue
            start,end=int(fields[3])-1,int(fields[4]);strand=fields[6]
            if not (0<=start<end<=sizes[fields[0]]) or strand not in ('+','-'):raise ValueError('Invalid GTF TSS reference')
            pos=start if strand=='+' else end-1
            if 2000<=pos<sizes[fields[0]]-2000:tss[fields[0]].add(pos)
    if not any(tss.values()):raise ValueError('No supported transcript TSS sites')
    return {chrom:sorted(values) for chrom,values in tss.items()}


def insertion_sites(start,end,size):
    left,right=start+4,end-5
    if start<0 or end<=start or end>size or not (0<=left<size and 0<=right<size):
        raise ValueError('Invalid unshifted fragment/Tn5 coordinates')
    return left,right


def tss_counts(cut,sites):
    center=bisect_right(sites,cut+50)-bisect_left(sites,cut-50)
    flank=bisect_right(sites,cut-1901)-bisect_left(sites,cut-2000)+bisect_right(sites,cut+2000)-bisect_left(sites,cut+1901)
    return center,flank


def record(read):
    return {'qname':read.query_name,'flag':read.flag,'chrom':read.reference_name,
            'position':read.reference_start,'mapq':read.mapping_quality,'cigar':read.cigarstring or '*',
            'tags':dict(read.get_tags())}


def check_header(header,sizes):
    if header.get('HD',{}).get('SO')!='queryname':raise ValueError('BAM must be queryname sorted')
    seq={}
    for row in header.get('SQ',[]):
        chrom,length=row['SN'],row['LN']
        if chrom in seq:raise ValueError('Duplicate BAM sequence')
        seq[chrom]=length
        if chrom in sizes and length!=sizes[chrom]:raise ValueError('BAM/mm10 length mismatch:'+chrom)
    if not set(CANONICAL+['chrM'])<=set(seq):raise ValueError('Missing canonical BAM reference sequences')


def candidate_cell(qname,pool,ligation,donors):
    match=re.match(r'^([ACGTN]{22}),',qname)
    if not match:return None,'invalid_QNAME_barcode'
    barcode=match[1]
    if barcode[:10] not in ligation:return None,'invalid_ligation_barcode'
    if barcode[10:] not in donors:return None,'unknown_TN5_donor_barcode'
    return pool+'.'+barcode,None


def output_usage(folder):
    folder=Path(folder);seen=set();used=0;inodes=0
    for root,dirs,files in os.walk(folder):
        inodes+=1
        for name in files:
            path=Path(root)/name
            try:st=path.stat()
            except FileNotFoundError:continue
            key=(st.st_dev,st.st_ino);seen.add(key)
            used+=max(st.st_size,st.st_blocks*512);inodes+=1
    # SQLite sort files can be unlinked while open. Inspect our own live FDs,
    # never a separate child/zombie PID. Count each physical inode only once.
    proc=Path('/proc/self/fd')
    if proc.is_dir():
        for fd in proc.iterdir():
            try:
                target=os.readlink(fd).removesuffix(' (deleted)');st=fd.stat()
            except FileNotFoundError:continue
            key=(st.st_dev,st.st_ino)
            if target.startswith(str(folder)+'/') and key not in seen:
                seen.add(key);used+=max(st.st_size,st.st_blocks*512);inodes+=1
    return used,inodes


def storage_check(folder,budget,inode_limit=100):
    used,inodes=output_usage(folder)
    if used>budget or inodes>inode_limit:raise ValueError('Own ATAC output/scratch budget exceeded')
    return used,inodes


def export_groups(groups,af,conn,pool,sizes,blacklist,ligation,donors,audit,per_cell,storage_guard=None):
    buffered=[]
    def flush():
        before=conn.total_changes
        conn.executemany('INSERT OR IGNORE INTO fragments VALUES(?,?,?,?)',buffered)
        added=conn.total_changes-before
        audit['retained_unique_fragments']+=added
        audit['excluded_coordinate_duplicates']+=len(buffered)-added
        buffered.clear();conn.commit()
        if storage_guard is not None:storage_guard()
    for qname,reads in groups:
        group=list(reads);audit['query_names_seen']+=1;audit['alignment_records_seen']+=len(group)
        cell,error=candidate_cell(qname,pool,ligation,donors)
        if error:audit[error]+=1;continue
        per_cell[cell]['query_names_seen']+=1
        value,status=af.fragment(group,sizes,set(CANONICAL),30,blacklist,'chrM')
        per_cell[cell][status]+=1;audit[status]+=1
        if value is not None:
            buffered.append((cell,*value))
            if len(buffered)>=50000:flush()
    flush()


def stored_fragments(conn,cells):
    # One external genomic sort, matching the established exporter. Its bounded
    # memory/temp files are monitored inside this pool's explicit working budget.
    for cell,chrom,start,end in conn.execute('SELECT cell,chrom,start,end FROM fragments ORDER BY chrom,start,end,cell'):
        yield {'chrom':chrom,'start':start,'end':end,'cell_id':cell}


def candidate_metadata(cells,per_cell,counts,donors,published,pool,args):
    for cell in cells:
        d=donors[cell.rsplit('.',1)[1][10:]];p=published.get(cell,{})
        q=counts[cell];eligible=per_cell[cell]['eligible_before_duplicate_removal'];retained=q['unique_fragments']
        if eligible<retained:raise ValueError('Fragment duplicate partition violated')
        if per_cell[cell]['query_names_seen']!=eligible+sum(per_cell[cell][key] for key in REASONS):raise ValueError('Disjoint filtering partition violated')
        tss=(q['tss_center_cut_count']/101)/(q['tss_flank_cut_count']/200) if q['tss_flank_cut_count'] else float('nan')
        nfr=q['nfr_fragments'];mono=q['mono_nucleosome_fragments']
        genotype='WT' if d['condition'].startswith('WT_') else ('5xFAD' if d['condition'].startswith('5xFAD') else 'APOE4/TREM2')
        if p and (p.get('animal_id')!=d['donor_id'] or p.get('condition')!=d['condition']):raise ValueError('Published calibration donor mismatch')
        row={'cell_id':cell,'animal_id':d['donor_id'],'donor_id':d['donor_id'],'condition':d['condition'],'age_months':d['age_months'],
             'sex':d['sex'],'replicate':d['replicate'],'replicate_id':d['replicate'],'genotype':genotype,'assay':'atac','library_id':pool,
             'technical_batch':pool,'published_whitelist':bool(p),'published_cell_type':p.get('published_cell_type','UNASSIGNED'),
             'cell_type_source':'GEO_GSM6538357_calibration' if p else 'fresh_candidate_unassigned',
             'candidate_source':'all_observed_validated_barcodes','unique_fragments':retained,
             'eligible_before_duplicate_removal':eligible,'excluded_coordinate_duplicates':eligible-retained,
             'tss_center_cut_count':q['tss_center_cut_count'],'tss_flank_cut_count':q['tss_flank_cut_count'],
             'tss_enrichment':tss,'tss_background_supported':q['tss_flank_cut_count']>0,
             'nfr_fragments':nfr,'mono_nucleosome_fragments':mono,'nucleosome_signal':mono/nfr if nfr else float('nan'),
             'fresh_mm10_qc_initial':retained>=args.min_unique_fragments and math.isfinite(tss) and tss>=args.min_tss_enrichment,
             'doublet_status':'not_yet_computed','frip':'NA','final_cell_selection':False}
        row.update({k:per_cell[cell][k] for k in ['query_names_seen']+REASONS})
        yield row


def extract(args):
    import pysam
    all_pools=pools(args.catalog)
    if args.index is None or not 0<=args.index<len(all_pools):raise ValueError('ATAC pool index outside catalog')
    pool,rows=all_pools[args.index]
    target=args.output/pool
    budget=args.max_output_bytes or max(20_000_000_000,4*sum(int(r['bytes']) for r in rows))
    if (target/'complete.json').exists():
        receipt=json.loads((target/'complete.json').read_text())
        if receipt.get('cell_selection')!=POLICY or receipt.get('catalog_sha256')!=sha(args.catalog):raise ValueError('Existing completion uses different inputs/policy')
        for name,pin in receipt['output_sha256'].items():
            if sha(target/name)!=pin:raise ValueError('Completed fragment/QC product changed')
        print(json.dumps({'status':'reused_complete_candidate_pool','pool':pool}));return
    if target.exists():raise ValueError('Incomplete output exists; preserve it and use a new output root:'+str(target))
    target.mkdir(parents=True);started=time.monotonic();af,sources=modules(args.project)
    ref,sizes=read_reference(args.reference_contract)
    donors=donor_lookup(args.donor_map);ligation=ligation_lookup(args.ligation_barcodes);published=published_lookup(args.published_metadata,pool)
    if sha(ref['files']['gtf']['path'])!=ref['files']['gtf']['sha256']:raise ValueError('M25 GTF checksum mismatch')
    tss=transcript_tss(ref['files']['gtf']['path'],sizes)
    blacklist=af.IntervalIndex(list(af.load_bed(ref['files']['blacklist']['path'])))
    (target/'tmp').mkdir()
    os.environ['SQLITE_TMPDIR']=str(target/'tmp');os.environ['TMPDIR']=str(target/'tmp')
    conn=sqlite3.connect(target/'atac_fragment_dedup.sqlite')
    conn.execute('PRAGMA journal_mode=WAL');conn.execute('PRAGMA synchronous=NORMAL');conn.execute('PRAGMA temp_store=FILE');conn.execute('PRAGMA cache_size=-65536')
    conn.execute('CREATE TABLE fragments(cell TEXT,chrom TEXT,start INTEGER,end INTEGER,PRIMARY KEY(cell,chrom,start,end)) WITHOUT ROWID')
    audit=Counter();per_cell=defaultdict(Counter);inputs=[]
    next_check=[0.0];budget_error=[]
    def sqlite_progress():
        if time.monotonic()>=next_check[0]:
            next_check[0]=time.monotonic()+5
            try:storage_check(target,budget,args.max_output_inodes)
            except ValueError as error:budget_error.append(str(error));return 1
        return 0
    conn.set_progress_handler(sqlite_progress,1_000_000)
    try:
        for row in rows:
            path=Path(row['queryname_bam']);before=bam_identity(path)
            if before[2]!=int(row['bytes']):raise ValueError('Catalog BAM length changed')
            subprocess.run([str(args.samtools),'quickcheck','-v',str(path)],check=True)
            with pysam.AlignmentFile(path,'rb',threads=args.bam_threads) as bam:
                check_header(bam.header.to_dict(),sizes)
                mapped=(record(read) for read in bam.fetch(until_eof=True))
                export_groups(itertools.groupby(mapped,key=lambda r:r['qname']),af,conn,pool,sizes,blacklist,ligation,donors,audit,per_cell,
                              lambda:storage_check(target,budget,args.max_output_inodes))
            if bam_identity(path)!=before:raise ValueError('Source complete multimapping BAM changed')
            inputs.append({'run':row['run'],'queryname_bam':str(path),'identity':before,'job_id':row['job_id'],'full_EOF_read':True})
        cells=sorted(per_cell);counts=defaultdict(Counter)
        for cell,chrom,start,end in conn.execute('SELECT cell,chrom,start,end FROM fragments ORDER BY cell,chrom,start,end'):
            q=counts[cell];q['unique_fragments']+=1;length=end-start
            q['nfr_fragments']+=length<147;q['mono_nucleosome_fragments']+=147<=length<=294
            for cut in insertion_sites(start,end,sizes[chrom]):
                center,flank=tss_counts(cut,tss.get(chrom,[]));q['tss_center_cut_count']+=center;q['tss_flank_cut_count']+=flank
        fragments=target/'audited_fragments.tsv.gz'
        write_table(fragments,['chrom','start','end','cell_id'],stored_fragments(conn,cells))
        storage_check(target,budget,args.max_output_inodes)
        metadata_rows=candidate_metadata(cells,per_cell,counts,donors,published,pool,args)
        first=next(metadata_rows,None)
        if first is None:raise ValueError('No valid donor-linked candidate cells')
        write_table(target/'candidate_cell_qc.tsv.gz',list(first),itertools.chain([first],metadata_rows))
        retained=sum(v['unique_fragments'] for v in counts.values())
        if retained!=audit['retained_unique_fragments']:raise ValueError('Retained per-cell/global fragment totals mismatch')
        missing=set(published)-set(cells)
        write_table(target/'published_cells_without_mapped_candidates.tsv',['cell_id'],({'cell_id':x} for x in sorted(missing)))
        summary={'pcr_id':pool,'assembly':'mm10','run_complete':True,'coordinate_system':COORDINATES,
                 'minimum_mapq':30,'required_nh':1,'blacklist_applied':True,'blacklist_assembly':'mm10',
                 'blacklist_sha256':ref['files']['blacklist']['sha256'],'reference_chrom_sizes_sha256':ref['files']['chrom_sizes']['sha256'],
                 'cell_selection':POLICY,'n_candidate_cells':len(cells),'n_cells_with_fragments':sum(v['unique_fragments']>0 for v in counts.values()),'audit':dict(audit),
                 'fragments_file':str(fragments),'fragments_sha256':sha(fragments),'no_Tn5_shift_in_fragments':True,
                 'TSS_definition':'Unique canonical M25 transcript TSS, boundary-complete +/-2000bp; +4/-5 cuts once; 101bp central /200bp flanks',
                 'dedup_key':'PCR pool.LIG10.N5+N7 barcode identity, chromosome, unshifted start,end; partitions merged before QC',
                 'fresh_doublet_QC_performed':False,'FRiP_computed':False,'final_cell_selection_performed':False}
        new_json(target/'fragment_export_audit.json',summary)
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)');conn.close();conn=None
        names=['audited_fragments.tsv.gz','candidate_cell_qc.tsv.gz','fragment_export_audit.json','published_cells_without_mapped_candidates.tsv']
        receipt={'status':'complete_all_candidate_pool_fragments_initial_QC','assembly':'mm10','pool':pool,'inputs':inputs,
                 'cell_selection':POLICY,'catalog_sha256':sha(args.catalog),'source_sha256':sources,'pysam_version':pysam.__version__,
                 'donor_map_sha256':sha(args.donor_map),'ligation_barcodes_sha256':sha(args.ligation_barcodes),
                 'published_calibration_sha256':sha(args.published_metadata),'reference_contract_sha256':sha(args.reference_contract),
                 'output_sha256':{name:sha(target/name) for name in names},'n_candidate_cells':len(cells),'unique_fragments':retained,
                 'published_cells_missing_mapped_candidates':len(missing),'elapsed_seconds':time.monotonic()-started,
                 'full_secondary_queryname_BAMs_preserved':True,'QC_filters_are_initial_not_final':True,
                 'storage_working_envelope_bytes':budget,'maximum_output_inodes':args.max_output_inodes,'physical_output_bytes':storage_check(target,budget,args.max_output_inodes)[0],'global_dedup':'All technical BAM partitions share this PCR pool database; distinct PCR pools keep distinct cell identities'}
        new_json(target/'complete.json',receipt);print(json.dumps({'status':receipt['status'],'pool':pool,'candidate_cells':len(cells),'unique_fragments':retained}))
    finally:
        if conn is not None:conn.close()


def merge(args):
    all_pools=pools(args.catalog)
    if len(all_pools)!=104:raise ValueError('Full-study merge requires104 distinct ATAC PCR pools')
    fragments=[];qc_paths=[];summary=[];metadata_fields=None
    for pool,rows in all_pools:
        folder=args.output/pool;receipt=json.loads((folder/'complete.json').read_text())
        if receipt.get('cell_selection')!=POLICY or receipt.get('catalog_sha256')!=sha(args.catalog):raise ValueError('Pool candidate policy/catalog differs')
        for name,pin in receipt['output_sha256'].items():
            if sha(folder/name)!=pin:raise ValueError('Completed pool product checksum changed')
        fragments.append({'path':str(folder/'audited_fragments.tsv.gz'),'pcr_id':pool,'sha256':receipt['output_sha256']['audited_fragments.tsv.gz'],'audit_path':str(folder/'fragment_export_audit.json')})
        qc_paths.append(folder/'candidate_cell_qc.tsv.gz');summary.append({'pool':pool,'candidate_cells':receipt['n_candidate_cells'],'unique_fragments':receipt['unique_fragments']})
    write_table(args.output/'complete_atac_fragment_manifest.tsv',list(fragments[0]),fragments)
    def all_cells():
        nonlocal metadata_fields
        for path in qc_paths:
            for row in table(path):
                if metadata_fields is None:metadata_fields=list(row)
                if list(row)!=metadata_fields:raise ValueError('Pool QC metadata columns differ')
                yield row
    iterator=all_cells();first=next(iterator)
    write_table(args.output/'candidate_cell_metadata.tsv.gz',metadata_fields,itertools.chain([first],iterator))
    write_table(args.output/'pool_summary.tsv',list(summary[0]),summary)
    new_json(args.output/'study_fragment_QC_complete.json',{'status':'104_pool_candidate_fragments_initial_QC_complete',
             'catalog_sha256':sha(args.catalog),'n_pools':104,'candidate_cells':sum(x['candidate_cells'] for x in summary),
             'unique_fragments':sum(x['unique_fragments'] for x in summary),'cell_selection':POLICY,
             'global_duplicate_handling':'Within PCR pool, all technical partitions deduplicated before QC; full PCR/barcode cell identity prevents cross-pool or cross-animal coordinate collapse',
             'final_cell_QC_complete':False,'doublets_and_FRiP_pending':True})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['extract','merge','plan']);p.add_argument('--project',type=Path,default=DEFAULT_PROJECT)
    p.add_argument('--catalog',type=Path);p.add_argument('--output',type=Path);p.add_argument('--index',type=int)
    p.add_argument('--reference-contract',type=Path);p.add_argument('--donor-map',type=Path);p.add_argument('--ligation-barcodes',type=Path)
    p.add_argument('--published-metadata',type=Path);p.add_argument('--samtools',type=Path);p.add_argument('--bam-threads',type=int,default=2)
    p.add_argument('--max-output-bytes',type=int);p.add_argument('--max-output-inodes',type=int,default=100)
    p.add_argument('--min-unique-fragments',type=int,default=1500);p.add_argument('--min-tss-enrichment',type=float,default=2.0)
    a=p.parse_args();a.catalog=a.catalog or a.project/'workflow/manual_alignment/completed_mapping_paths_20261008.tsv'
    a.output=a.output or a.project/'results/mm10/full_study_20261008/atac_candidates'
    a.reference_contract=a.reference_contract or a.project/'references/mm10/reference_contract.json'
    a.donor_map=a.donor_map or a.project/'metadata/atac_tn5_barcode_to_donor.tsv'
    a.ligation_barcodes=a.ligation_barcodes or a.project/'workflow/vendor/EasySci_original/Supplementary_Code_2/EasySci_ATAC_pipeline/Scripts/EasySci-ATAC_P5_BC.txt'
    a.published_metadata=a.published_metadata or a.project/'workflow/downstream/atac_cell_metadata.normalized.tsv.gz'
    a.samtools=a.samtools or a.project/'software/envs/preprocess/bin/samtools'
    if a.stage=='plan':
        groups=pools(a.catalog);print(json.dumps({'pools':[{'index':i,'pool':pool,'runs':[r['run'] for r in rows],'BAM_bytes':sum(int(r['bytes']) for r in rows)} for i,(pool,rows) in enumerate(groups)],
          'n_pools':len(groups),'n_ATAC_BAMs':sum(len(rows) for _,rows in groups),'BAM_bytes':sum(int(r['bytes']) for _,rows in groups for r in rows),
          'conservative_total_output_and_scratch_bytes':3*sum(int(r['bytes']) for _,rows in groups for r in rows),'cell_selection':POLICY,
          'ATAC0_existing_whitelist_export':'retain calibration product; it cannot cover all observed candidates, so only downstream candidate fragment extraction is necessary; no remapping'},indent=2));return
    a.output.mkdir(parents=True,exist_ok=True)
    if a.stage=='extract':extract(a)
    else:merge(a)


if __name__=='__main__':main()
