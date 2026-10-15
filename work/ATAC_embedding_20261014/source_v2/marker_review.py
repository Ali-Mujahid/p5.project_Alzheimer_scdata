"""Independent raw gene-body accessibility diagnostics; no cell-type calls."""
import sys
sys.dont_write_bytecode=True
import json,pathlib
import numpy as np,pandas as pd,anndata as ad
from scipy import sparse

def aggregate(raw,totals,codes,n_groups):
 if not sparse.issparse(raw) or not np.issubdtype(raw.dtype,np.integer) or (raw.data<0).any():raise ValueError('Nonnegative sparse integer activity counts required')
 if len(codes)!=raw.shape[0] or len(totals)!=raw.shape[0] or (codes<0).any() or (codes>=n_groups).any():raise ValueError('Activity membership differs')
 membership=sparse.csr_matrix((np.ones(len(codes),dtype=np.int64),(codes,np.arange(len(codes)))),shape=(n_groups,len(codes)))
 norm=(sparse.diags(np.divide(1e4,totals,out=np.zeros(len(totals)),where=totals>0))@raw).tocsr();norm.data=np.log1p(norm.data)
 return (membership@raw).toarray(),(membership@(raw>0)).toarray(),(membership@norm).toarray()

def main():
 atlas,activity,out=map(pathlib.Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
 e=ad.read_h5ad(atlas,backed='r');a=ad.read_h5ad(activity,backed='r')
 if not e.obs_names.equals(a.obs_names):raise ValueError('Peak atlas and activity cell order differ')
 if a.uns.get('feature_space')!='activity' or a.uns.get('genome')!='GRCm38/mm10':raise ValueError('Independent mm10 gene-body accessibility required')
 panels=json.loads((pathlib.Path(__file__).parent/'marker_panels.json').read_text());genes=list(dict.fromkeys(g for v in panels.values() for g in v));symbols=a.var.gene_symbol.astype('string').fillna('');ix=np.flatnonzero(symbols.isin(genes).to_numpy());mapping=pd.Index(genes).get_indexer(symbols.iloc[ix]);collapse=sparse.csr_matrix((np.ones(len(ix),dtype=np.int64),(np.arange(len(ix)),mapping)),shape=(len(ix),len(genes)))
 pd.DataFrame([{'gene_symbol':g,'n_features':int((symbols==g).sum()),'present':bool((symbols==g).any())} for g in genes]).to_csv(out/'symbol_audit.tsv',sep='\t',index=False)
 keys=pd.MultiIndex.from_frame(e.obs[['initial_cluster','animal_id']].astype(str));codes,groups=pd.factorize(keys,sort=True);n=np.bincount(codes);shape=(len(groups),len(genes));rawsum=np.zeros(shape,np.int64);detect=np.zeros(shape,np.int64);logs=np.zeros(shape);zero=0
 for start in range(0,a.n_obs,10000):
  stop=min(a.n_obs,start+10000);x=a.X[start:stop].tocsr();totals=np.asarray(x.sum(axis=1)).ravel().astype(float);zero+=int((totals==0).sum());raw=(x[:,ix]@collapse).tocsr();u,d,l=aggregate(raw,totals,codes[start:stop],len(groups));rawsum+=u;detect+=d;logs+=l;print('activity_rows',stop,flush=True)
 rows=[]
 for i,(cluster,animal) in enumerate(groups):
  for panel,markers in panels.items():
   for gene in markers:
    j=genes.index(gene);rows.append({'initial_cluster':cluster,'animal_id':animal,'n_cells':int(n[i]),'panel':panel,'gene_symbol':gene,'raw_integer_activity_sum':int(rawsum[i,j]),'fraction_activity_detected':float(detect[i,j]/n[i]),'mean_log1p_activity_per10k':float(logs[i,j]/n[i])})
 t=pd.DataFrame(rows);t.to_csv(out/'markers_by_cluster_animal.tsv',sep='\t',index=False)
 t.groupby(['initial_cluster','panel','gene_symbol'],observed=True).agg(equal_animal_mean_log1p_activity=('mean_log1p_activity_per10k','mean'),equal_animal_detection=('fraction_activity_detected','mean'),n_animals=('animal_id','nunique')).reset_index().to_csv(out/'equal_animal_markers.tsv',sep='\t',index=False)
 e.obs.groupby(['initial_cluster','animal_id','library_id','condition'],observed=True).size().rename('n_cells').to_csv(out/'cluster_coverage.tsv',sep='\t')
 qc=[f for f in ['unique_fragments','tss_enrichment','frip','nucleosome_signal','qc_total_counts','qc_detected_features'] if f in e.obs]
 e.obs.groupby(['initial_cluster','library_id'],observed=True)[qc].quantile([.01,.05,.5,.95,.99]).to_csv(out/'cluster_library_QC_quantiles.tsv',sep='\t')
 comparison={}
 if 'initial_cluster_uncorrected' in e.obs:
  from sklearn.metrics import adjusted_rand_score
  comparison={'ARI_corrected_vs_same_LSI_uncorrected':float(adjusted_rand_score(e.obs.initial_cluster,e.obs.initial_cluster_uncorrected))}
 (out/'complete.json').write_text(json.dumps({'n_cells':a.n_obs,'panel_genes':len(genes),'zero_total_activity_cells':zero,'counts_source':'raw integer GENCODE M25 gene-body fragment accessibility; not RNA expression','normalized_statistics':'descriptive log1p activity per10k using full gene-body activity denominator; equal animal weight','cell_types_assigned':False,'exclusions_applied':False,'final_annotation_complete':False,'missing_gene_does_not_prove_absence':True,**comparison},indent=2)+'\n')
 e.file.close();a.file.close()
if __name__=='__main__':main()
