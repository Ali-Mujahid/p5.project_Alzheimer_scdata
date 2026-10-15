"""Narrow reviewed Harmony layout bridge and PCR design audit for RNA."""
import hashlib
import importlib.metadata
import json
import numpy as np
import pandas as pd
from core import validate_obs,validate_technical_batch,require_counts

SUPPORTED_LAYOUTS={'2.0.0':'cells_by_pcs','0.0.10':'pcs_by_cells'}


def raw_csr_digest(x):
    x=require_counts(x)
    h=hashlib.sha256(json.dumps({'shape':x.shape,'dtype':str(x.dtype)},sort_keys=True).encode())
    for name in ('data','indices','indptr'):
        values=getattr(x,name)
        if not values.flags.c_contiguous:raise ValueError('Raw CSR array must be contiguous for exact audit')
        h.update(name.encode());h.update(str(values.dtype).encode())
        view=memoryview(values).cast('B')
        for start in range(0,len(view),8*1024*1024):h.update(view[start:start+8*1024*1024])
    return h.hexdigest()


def pcr_design(obs,batch_key='library_id',expected_animals=20):
    validate_obs(obs)
    if batch_key!='library_id':raise ValueError('This RNA adapter corrects verified PCR library_id only')
    validate_technical_batch(obs,batch_key)
    if 'donor_id' not in obs or not obs.donor_id.astype(str).equals(obs.animal_id.astype(str)):raise ValueError('Donor/animal aliases must agree for RNA PCR correction')
    donors=obs.animal_id.astype(str);libraries=obs[batch_key].astype(str)
    table=pd.crosstab(libraries,donors)
    if len(table.columns)!=expected_animals:raise ValueError('Expected all20 verified animal identities before full-study RNA correction')
    if (table.gt(0).sum(axis=0)<2).any() or (table.gt(0).sum(axis=1)<2).any():raise ValueError('Animal/PCR coverage is insufficient to separate library and donor')
    # A connected library-donor bipartite design prevents disconnected biology.
    remaining=set(table.columns);seen=set();frontier={next(iter(remaining))}
    while frontier:
        seen.update(frontier);used=table.index[table[list(frontier)].gt(0).any(axis=1)]
        connected=set(table.columns[table.loc[used].gt(0).any(axis=0)])
        frontier=connected-seen
    if len(seen)!=len(remaining):raise ValueError('PCR/donor design is disconnected; library effects are not identifiable across animals')
    return {'method':'PCR library correction with connected animal/PCR coverage',
            'n_animals':len(table.columns),'n_libraries':len(table),
            'min_libraries_per_animal':int(table.gt(0).sum(axis=0).min()),
            'min_animals_per_library':int(table.gt(0).sum(axis=1).min()),
            'condition_by_library':pd.crosstab(libraries,obs.condition).to_dict(),
            'donor_by_library':table.to_dict(),'identifiable':True}


def checked_harmony(pc,obs,batch_key,*,version,run_harmony,seed=1729,ncores=1):
    layout=SUPPORTED_LAYOUTS.get(version)
    if layout is None:raise ValueError('Unreviewed harmonypy version: '+str(version))
    if ncores<1:raise ValueError('An explicit positive allocated Harmony thread count is required')
    matrix=np.array(pc,dtype=np.float64,order='C',copy=True)
    if matrix.ndim!=2 or matrix.shape[0]!=len(obs) or matrix.shape[0]<=matrix.shape[1] or not np.isfinite(matrix).all():raise ValueError('Harmony requires finite nonsquare cells-by-PCs with more cells than PCs')
    original=hashlib.sha256(memoryview(matrix).cast('B')).hexdigest()
    kwargs={'random_state':seed,'verbose':True}
    if version=='2.0.0':kwargs['ncores']=ncores
    result=run_harmony(matrix,obs,batch_key,**kwargs)
    corrected=np.asarray(result.Z_corr)
    expected=matrix.shape if layout=='cells_by_pcs' else matrix.shape[::-1]
    if corrected.shape!=expected or not np.isfinite(corrected).all():raise ValueError('Harmony corrected shape/layout or finite-value contract failed')
    if layout=='pcs_by_cells':corrected=corrected.T
    return np.array(corrected,dtype=np.float32,order='C',copy=True),{
        'harmonypy_version':version,'reviewed_output_layout':layout,'stored_layout':'cells_by_pcs',
        'seed':seed,'allocated_threads':ncores,'input_pc_sha256':original,
        'input_shape':list(matrix.shape),'corrected_shape':list(corrected.shape),
        'input_array_private_copy':True}


def integrate(e,batch_key,*,basis='X_pca',adjusted_basis='X_pca_harmony',seed=1729,ncores=1):
    import harmonypy
    version=importlib.metadata.version('harmonypy')
    reported=getattr(harmonypy,'__version__',version)
    if reported!=version:raise ValueError('Loaded harmonypy module/version metadata disagree')
    corrected,provenance=checked_harmony(e.obsm[basis],e.obs,batch_key,
                                       version=version,run_harmony=harmonypy.run_harmony,
                                       seed=seed,ncores=ncores)
    e.obsm[adjusted_basis]=corrected
    return provenance
