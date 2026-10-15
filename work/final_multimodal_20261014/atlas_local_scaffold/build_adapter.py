from pathlib import Path
import csv,json,hashlib,datetime,math,gzip
ROOT=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a')
SRC=ROOT/'outputs/p5_workflow/ATAC_initial_atlas_20261014/job-7466270'
OUT=ROOT/'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
files=['marker_review/markers_by_cluster_animal.tsv','marker_review/equal_animal_markers.tsv','marker_review/symbol_audit.tsv','marker_review/cluster_coverage.tsv','annotation_review/provisional_cluster_annotation.tsv','annotation_review/cluster8_animal_denominators.tsv','download_manifest.actual.json','product_header_review.actual.json','terminal_observation.actual.json']
def rows(f):
 with open(SRC/f) as h:return list(csv.DictReader(h,delimiter='\t'))
proof=[]
for f in files:
 p=SRC/f;b=p.read_bytes();proof.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
animals={}
for r in rows(files[5]):
 a=r['animal_id'];c=r['condition'];sex=r['sex'];g='WT' if c.startswith('WT_') else ('5xFAD' if c.startswith('5xFAD_') else 'APOE4_TREM2')
 animals[a]={'id':a,'condition':c,'genotype':g,'sex':sex,'n_initial_cells':int(r['n_initial_cells'])}
assert len(animals)==20
coverage={}
for r in rows(files[3]):
 c=r['initial_cluster'];a=r['animal_id'];assert animals[a]['condition']==r['condition']
 coverage[c,a]=coverage.get((c,a),0)+int(r['n_cells'])
assert len(coverage)==220 and sum(coverage.values())==456472
symbols={r['gene_symbol']:r['present']=='True' for r in rows(files[2])}
genes=sorted(symbols)
panels={};unique={};duplicates=0
for r in rows(files[0]):
 c,a,g=r['initial_cluster'],r['animal_id'],r['gene_symbol'];n=int(r['n_cells']);s=int(r['raw_integer_activity_sum']);d=float(r['fraction_activity_detected']);v=float(r['mean_log1p_activity_per10k']);assert n==coverage[c,a] and n>0 and s>=0 and 0<=d<=1 and v>=0 and all(map(math.isfinite,[d,v]))
 value=[n,s,d,v];key=c,a,g
 if key in unique: assert unique[key]==value;duplicates+=1
 unique[key]=value
 panels.setdefault(r['panel'],set()).add(g)
assert len(unique)==11*20*107
# Recompute exact equal-animal means from actual per-animal table.
for r in rows(files[1]):
 c,g=r['initial_cluster'],r['gene_symbol'];vals=[unique[c,a,g] for a in animals]
 assert abs(sum(v[2] for v in vals)/20-float(r['equal_animal_detection']))<1e-12
 assert abs(sum(v[3] for v in vals)/20-float(r['equal_animal_mean_log1p_activity']))<1e-12
clusters=[]
for r in rows(files[4]):
 clusters.append({'id':r['initial_cluster'],'n':int(r['n_cells']),'candidate':r['candidate_annotation'],'status':r['status'],'evidence':r['evidence_genes'].split(';'),'frip':float(r['median_FRiP']),'tss':float(r['median_TSS']),'fragments':float(r['median_fragments']),'next':r['review_next']})
clusters.sort(key=lambda x:int(x['id']))
assert sum(x['n'] for x in clusters)==456472
# Header only: the downloaded producer metadata has no 2-D embedding coordinates.
with gzip.open(SRC/'embedding/initial_cell_metadata.tsv.gz','rt') as h: header=h.readline().rstrip('\n').split('\t')
assert not any('umap' in x.lower() for x in header)
records=[[int(c),a,g,*v] for (c,a,g),v in sorted(unique.items(),key=lambda x:(int(x[0][0]),x[0][1],x[0][2]))]
D={'schema_version':'1.0','dataset_id':'ATAC_initial_7466270','title':'GSE212606 · initial ATAC atlas','provisional':True,'job_id':'7466270','producer_completed_utc':'2026-10-14T08:22:39Z','n_cells':456472,'n_peaks':68126,'all_cell_types':True,'final_labels_available':False,'final_qc_available':False,'umap_coordinates_available':(OUT/'coordinate_provenance.actual.json').exists(),'raw_CSR_read':False,'animals':list(animals.values()),'clusters':clusters,'genes':[{'symbol':g,'mapped':symbols[g]} for g in genes],'panels':{k:sorted(v) for k,v in sorted(panels.items())},'record_columns':['cluster','animal','gene','n_cells','raw_integer_activity_sum','fraction_activity_detected','mean_log1p_activity_per10k'],'records':records,'source_records':proof,'pdfs':[{'label':'Harmony · clusters and conditions','path':'../../ATAC_initial_atlas_20261014/job-7466270/embedding/umap_initial_diagnostic_clusters_conditions.pdf'},{'label':'Uncorrected · same LSI','path':'../../ATAC_initial_atlas_20261014/job-7466270/embedding/umap_uncorrected_same_LSI_clusters_conditions.pdf'},{'label':'Animals and libraries','path':'../../ATAC_initial_atlas_20261014/job-7466270/embedding/umap_initial_diagnostic_animals_libraries.pdf'},{'label':'Published calibration only','path':'../../ATAC_initial_atlas_20261014/job-7466270/embedding/umap_initial_diagnostic_calibration_labels.pdf'}],'status':{'ATAC gene-body activity':'Initial results available; final QC / doublet review pending','RNA genes':'Final filtered SCT workflow pending; no RNA scatter adapter in this preview','RNA TE expression':'Not yet produced','ATAC TE accessibility':'Not yet produced','Coverage / tracks':'Not yet produced','Final cell-type labels':'Independent review pending'}}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'data_adapter.js').write_text('/* Generated from accepted small tables; never contains raw CSR. */\nwindow.ATLAS_DATA='+json.dumps(D,separators=(',',':'),allow_nan=False)+';\n')
proof_out={'built_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dataset':D['dataset_id'],'n_cells':456472,'n_unique_cluster_animal_gene_records':len(records),'identical_duplicate_panel_rows_collapsed':duplicates,'n_genes':107,'n_unmapped_genes':sum(not x for x in symbols.values()),'animals':20,'clusters':11,'equal_animal_saved_summary_parity':True,'metadata_header_only_read':True,'metadata_coordinates_present':False,'raw_CSR_read':False,'inputs':proof,'data_adapter_sha256':hashlib.sha256((OUT/'data_adapter.js').read_bytes()).hexdigest()}
(OUT/'build_provenance.actual.json').write_text(json.dumps(proof_out,indent=2)+'\n')
print(json.dumps({k:v for k,v in proof_out.items() if k!='inputs'},indent=2))
