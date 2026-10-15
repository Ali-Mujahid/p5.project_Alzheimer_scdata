from pathlib import Path
import h5py,numpy as np,gzip,csv,json,hashlib,base64,datetime
ROOT=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a');SRC=ROOT/'outputs/p5_workflow/ATAC_initial_atlas_20261014/job-7466270';OUT=ROOT/'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
p=SRC/'embedding/atac_initial_atlas.h5ad';manifest=json.load(open(SRC/'download_manifest.actual.json'));rec=next(x for x in manifest['records'] if x['relative_path']=='embedding/atac_initial_atlas.h5ad');assert p.stat().st_size==rec['bytes']
animals=[r['animal_id'] for r in csv.DictReader(open(SRC/'annotation_review/cluster8_animal_denominators.tsv'),delimiter='\t')];amap={x:i for i,x in enumerate(animals)}
def decode(x):return x.decode() if isinstance(x,bytes) else str(x)
outputs=[];N=456472;attrs=np.empty((N,3),dtype=np.uint8);idhash=hashlib.sha256();count=0
with h5py.File(p,'r') as f:
 idx=f['obs'][f['obs'].attrs['_index']];assert idx.shape==(N,)
 with gzip.open(SRC/'embedding/initial_cell_metadata.tsv.gz','rt') as h:
  reader=csv.DictReader(h,delimiter='\t');ids=None
  for i,r in enumerate(reader):
   if i%4096==0:ids=idx[i:min(N,i+4096)]
   assert r['cell_id']==decode(ids[i%4096]),(i,r['cell_id'])
   idhash.update((r['cell_id']+'\n').encode());attrs[i]=[int(r['initial_cluster']),int(r['initial_cluster_uncorrected']),amap[r['animal_id']]];count+=1
 assert count==N and attrs[:,0].max()==10 and attrs[:,1].max()==8
 for key,name in [('X_umap_initial','harmony'),('X_umap_initial_uncorrected','uncorrected')]:
  d=f['obsm'][key];assert d.shape==(N,2);a=d[:].astype('<f4',copy=False);assert np.isfinite(a).all();b=a.tobytes(order='C');path=OUT/f'coordinates_{name}.js';path.write_text('/* Bounded producer obsm coordinate export; no graph calculation. */\nwindow.ATLAS_COORDINATES=window.ATLAS_COORDINATES||{};\nwindow.ATLAS_COORDINATES['+json.dumps(name)+']='+json.dumps({'n':N,'dimensions':2,'dtype':'float32-little-endian','base64':base64.b64encode(b).decode()},separators=(',',':'))+';\n');outputs.append({'file':path.name,'dataset':'/obsm/'+key,'shape':list(a.shape),'source_dtype':str(d.dtype),'export_dtype':str(a.dtype),'derived_bytes_sha256':hashlib.sha256(b).hexdigest(),'file_bytes':path.stat().st_size})
b=attrs.tobytes();(OUT/'point_attributes.js').write_text('window.ATLAS_POINT_ATTRIBUTES='+json.dumps({'n':N,'columns':['cluster','uncorrected_cluster','animal_index'],'dtype':'uint8','animals':animals,'base64':base64.b64encode(b).decode()},separators=(',',':'))+';\n')
proof={'exported_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(p),'source_local_bytes':p.stat().st_size,'accepted_remote_identity':rec['remote_identity'],'read_datasets':['/obsm/X_umap_initial','/obsm/X_umap_initial_uncorrected','/obs/cell_id'],'source_metadata':str(SRC/'embedding/initial_cell_metadata.tsv.gz'),'exact_metadata_H5_cell_id_order':True,'n_rows':N,'ordered_cell_ids_sha256':idhash.hexdigest(),'graph_recomputed':False,'raw_X_CSR_read':False,'large_source_content_hash_computed':False,'coordinate_outputs':outputs,'attribute_bytes_sha256':hashlib.sha256(b).hexdigest(),'all_points_exported':True}
(OUT/'coordinate_provenance.actual.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ['accepted_remote_identity']},indent=2))
