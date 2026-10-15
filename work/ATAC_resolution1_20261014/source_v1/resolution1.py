"""Additive Leiden1 labels on saved ATAC graphs, then new raw activity summaries."""
import sys
sys.dont_write_bytecode = True
import gc
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import numpy as np
import pandas as pd
import h5py
import anndata as ad
from anndata.io import read_elem
from scipy import sparse
import scanpy as sc
import leidenalg
import frozen_marker_review

SRC = Path(__file__).resolve().parent


def need(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def graph_digest(graph):
    h = hashlib.sha256()
    h.update(str((graph.shape, graph.dtype.str)).encode())
    for part in [graph.data, graph.indices, graph.indptr]:
        h.update(str((part.shape, part.dtype.str)).encode()); h.update(memoryview(part))
    return h.hexdigest()


def read_obs_only(path, access):
    with h5py.File(path, 'r') as handle:
        access.append('/obs')
        obs = read_elem(handle['obs'])
    need(isinstance(obs, pd.DataFrame) and obs.index.is_unique and not obs.index.hasnans,
         'Atlas obs is not uniquely indexed metadata')
    obs.index = obs.index.astype(str)
    if 'cell_id' in obs:
        need(np.array_equal(obs.cell_id.astype(str).to_numpy(), obs.index.to_numpy()),
             'Canonical obs cell_id column and axis differ')
    return obs


def read_graph_only(path, key, expected_n, expected_nnz, access):
    with h5py.File(path, 'r') as handle:
        group = handle['obsp'][key]
        encoding = group.attrs['encoding-type']
        if isinstance(encoding, bytes): encoding = encoding.decode()
        need(encoding == 'csr_matrix' and tuple(group.attrs['shape']) == (expected_n, expected_n),
             'Saved graph encoding/shape differs from accepted graph')
        need(group['data'].shape == (expected_nnz,) and str(group['data'].dtype) == 'float32',
             'Saved graph nnz/dtype differs from accepted graph')
        access.append('/obsp/' + key)
        graph = read_elem(group)
    need(sparse.isspmatrix_csr(graph) and graph.shape == (expected_n, expected_n)
         and graph.nnz == expected_nnz and graph.dtype == np.float32,
         'Graph reader changed accepted sparse representation')
    graph.check_format(full_check=True)
    need(np.isfinite(graph.data).all() and (graph.data >= 0).all(), 'Graph has nonfinite/negative weights')
    return graph


def cluster_graph(graph, cell_ids, policy, key):
    before = graph_digest(graph)
    # This object has zero features. The study peak X matrix is never accessed.
    obj = ad.AnnData(sparse.csr_matrix((len(cell_ids), 0), dtype=np.float32),
                     obs=pd.DataFrame(index=cell_ids.copy()))
    args = dict(policy['leiden'])
    args.pop('partition_type')
    sc.tl.leiden(obj, adjacency=graph, partition_type=leidenalg.RBConfigurationVertexPartition,
                 key_added=key, **args)
    labels = obj.obs[key].astype(str).copy()
    need(labels.index.equals(cell_ids) and not labels.isna().any(), 'Leiden changed cell membership/order')
    after = graph_digest(graph)
    need(before == after, 'Leiden mutated the loaded sparse graph')
    del obj
    gc.collect()
    return labels, {'before_sha256': before, 'after_sha256': after, 'unchanged': True}


def verify_runtime(policy):
    versions = {name: importlib.metadata.version(name) for name in policy['runtime_versions']}
    need(versions == policy['runtime_versions'], 'Actual graph runtime differs from pinned versions')
    signature = inspect.signature(sc.tl.leiden)
    need(signature.parameters['flavor'].default == 'leidenalg'
         and signature.parameters['n_iterations'].default == -1
         and signature.parameters['directed'].default is None,
         'Scanpy Leiden API defaults differ from inspected1.11.5 API')
    source = Path(inspect.getsourcefile(sc.tl.leiden))
    return {'versions': versions, 'leiden_signature': str(signature), 'leiden_source_file': str(source),
            'leiden_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'explicit_parameters': policy['leiden']}


def synthetic_fixture(out, policy):
    out.mkdir(exist_ok=False)
    ids = pd.Index([f'synthetic_cell_{i:02d}' for i in range(12)], name='cell_id')
    graphs, groups = {}, {}
    for branch, size in [('corrected', 6), ('uncorrected', 4)]:
        parts = [np.ones((size, size), dtype=np.float32) - np.eye(size, dtype=np.float32)
                 for _ in range(12 // size)]
        graphs[branch] = sparse.block_diag(parts, format='csr', dtype=np.float32)
        groups[branch] = np.arange(12) // size
    obj = ad.AnnData(sparse.csr_matrix((12, 0), dtype=np.int32), obs=pd.DataFrame(index=ids))
    for branch, graph in graphs.items(): obj.obsp[policy['graphs'][branch]['key']] = graph
    fixture = out / 'synthetic_graphs.h5ad'; obj.write_h5ad(fixture)
    del obj
    access, checks = [], {}
    obs = read_obs_only(fixture, access)
    checks['exact_obs_order'] = obs.index.equals(ids)
    for branch, reference in graphs.items():
        graph = read_graph_only(fixture, policy['graphs'][branch]['key'], 12, reference.nnz, access)
        labels, preservation = cluster_graph(graph, ids, policy, 'resolution1')
        repeated, _ = cluster_graph(graph, ids, policy, 'resolution1')
        same = labels.to_numpy()[:, None] == labels.to_numpy()[None, :]
        wanted = groups[branch][:, None] == groups[branch][None, :]
        checks[branch + '_expected_disconnected_partition'] = bool(np.array_equal(same, wanted))
        checks[branch + '_seed_repeat_exact'] = labels.equals(repeated)
        checks[branch + '_graph_preserved'] = preservation['unchanged']
        del graph
    raw = sparse.csr_matrix(np.array([[1,0],[0,2],[3,1],[1,2]], dtype=np.int32))
    before = graph_digest(raw); codes = np.array([0,0,1,1]); totals = np.array([1,2,4,3.])
    sums, detected, logs = frozen_marker_review.aggregate(raw, totals, codes, 2)
    checks['actual_frozen_marker_aggregate_integer_sum'] = bool(np.array_equal(sums, np.array([[1,2],[4,3]])))
    checks['actual_frozen_marker_aggregate_detection'] = bool(np.array_equal(detected, np.array([[1,1],[2,2]])))
    checks['actual_frozen_marker_aggregate_finite'] = bool(np.isfinite(logs).all())
    checks['marker_raw_sparse_preserved'] = before == graph_digest(raw)
    checks['whitelist_never_read_X'] = all(name == '/obs' or name.startswith('/obsp/') for name in access)
    need(all(checks.values()), 'Actual synthetic Leiden/reader/aggregation fixture failed')
    save(out / 'complete.json', {'synthetic_only': True, 'status': 'passed', 'cells': 12,
         'checks': checks, 'accessed_input_groups': access, 'resolution': 1.0, 'seed': 1729,
         'study_clustering_completed': False})
    gc.collect()


def emit_coverage(obs, branch, spec, out):
    new, old = spec['new_cluster'], spec['old_cluster']
    prefix = branch + '_resolution1'
    columns = ['animal_id', 'library_id', 'condition', 'genotype', 'sex']
    for field in columns:
        pd.crosstab(obs[new], obs[field], dropna=False).to_csv(out / f'{prefix}_by_{field}.tsv', sep='\t')
    pd.crosstab(obs[old], obs[new], dropna=False).to_csv(out / f'{branch}_resolution0_6_vs_1_contingency.tsv', sep='\t')
    obs.groupby([new, 'animal_id', 'library_id', 'condition'], observed=True).size().rename('n_cells').to_csv(
        out / f'{prefix}_animal_library_condition_coverage.tsv', sep='\t')
    metrics = ['unique_fragments', 'tss_enrichment', 'frip', 'nucleosome_signal',
               'qc_total_counts', 'qc_detected_features', 'qc_pct_mt_query_groups']
    obs.groupby(new, observed=True)[metrics].quantile([.01,.05,.25,.5,.75,.95,.99]).to_csv(
        out / f'{prefix}_QC_quantiles.tsv', sep='\t')
    obs.groupby([new, 'animal_id'], observed=True)[metrics].quantile([.05,.5,.95]).to_csv(
        out / f'{prefix}_animal_QC_quantiles.tsv', sep='\t')
    summary = obs.groupby(new, observed=True).agg(n_cells=(new,'size'), n_animals=('animal_id','nunique'),
                      n_libraries=('library_id','nunique'), n_conditions=('condition','nunique'))
    need(int(summary.n_cells.sum()) == len(obs), 'Resolution1 cluster coverage lost cells')
    summary.to_csv(out / f'{prefix}_cluster_summary.tsv', sep='\t')
    return {'n_clusters': len(summary), 'n_cells': len(obs), 'old_cluster_key': old, 'new_cluster_key': new}


def markers(obs, policy, out):
    # Deliberate new activity pass for new memberships; no old marker means reused.
    out.mkdir(exist_ok=False)
    activity = ad.read_h5ad(policy['activity']['path'], backed='r')
    try:
        need(activity.obs_names.astype(str).equals(obs.index), 'Activity and graph cell axes/order differ')
        need(activity.uns.get('feature_space') == 'activity' and activity.uns.get('genome') == 'GRCm38/mm10',
             'Raw mm10 independent gene-body activity required')
        panels = json.loads((SRC / 'marker_panels.json').read_text())
        genes = list(dict.fromkeys(g for panel in panels.values() for g in panel))
        need(len(genes) == policy['marker_genes_expected'], 'Frozen panel size changed')
        symbols = activity.var.gene_symbol.astype('string').fillna('')
        indices = np.flatnonzero(symbols.isin(genes).to_numpy())
        mapping = pd.Index(genes).get_indexer(symbols.iloc[indices])
        collapse = sparse.csr_matrix((np.ones(len(indices), np.int64), (np.arange(len(indices)), mapping)),
                                     shape=(len(indices), len(genes)))
        present = {g: bool((symbols == g).any()) for g in genes}
        audit = pd.DataFrame([{'gene_symbol': g, 'n_features': int((symbols == g).sum()), 'present': present[g]}
                              for g in genes])
        branch_state = {}
        for branch, spec in policy['graphs'].items():
            key = spec['new_cluster']
            codes, groups = pd.factorize(pd.MultiIndex.from_frame(obs[[key, 'animal_id']].astype(str)), sort=True)
            shape = (len(groups), len(genes))
            branch_state[branch] = {'codes': codes, 'groups': groups, 'n': np.bincount(codes),
                                    'raw': np.zeros(shape, np.int64), 'detect': np.zeros(shape, np.int64),
                                    'logs': np.zeros(shape, np.float64)}
        zeros = 0
        for start in range(0, activity.n_obs, policy['activity_block_rows']):
            stop = min(activity.n_obs, start + policy['activity_block_rows'])
            block = activity.X[start:stop].tocsr()
            need(np.issubdtype(block.dtype, np.integer) and (block.data >= 0).all(), 'Activity is not raw nonnegative integer counts')
            totals = np.asarray(block.sum(axis=1)).ravel().astype(float)
            zeros += int((totals == 0).sum())
            raw = (block[:,indices] @ collapse).tocsr()
            for branch, state in branch_state.items():
                u, d, l = frozen_marker_review.aggregate(raw, totals, state['codes'][start:stop], len(state['groups']))
                state['raw'] += u; state['detect'] += d; state['logs'] += l
            del block, raw
            print('activity_rows', stop, flush=True)
        for branch, state in branch_state.items():
            destination = out / branch; destination.mkdir()
            audit.to_csv(destination / 'symbol_audit.tsv', sep='\t', index=False)
            rows = []
            for i, (cluster, animal) in enumerate(state['groups']):
                for panel, panel_genes in panels.items():
                    for gene in panel_genes:
                        j = genes.index(gene); n = int(state['n'][i])
                        rows.append({'initial_cluster': cluster, 'animal_id': animal, 'n_cells': n, 'panel': panel,
                                     'gene_symbol': gene, 'raw_integer_activity_sum': int(state['raw'][i,j]) if present[gene] else pd.NA,
                                     'fraction_activity_detected': float(state['detect'][i,j]/n) if present[gene] else np.nan,
                                     'mean_log1p_activity_per10k': float(state['logs'][i,j]/n) if present[gene] else np.nan})
            table = pd.DataFrame(rows); table.raw_integer_activity_sum = table.raw_integer_activity_sum.astype('Int64')
            table.to_csv(destination / 'markers_by_cluster_animal.tsv', sep='\t', index=False, na_rep='NA')
            equal = table.groupby(['initial_cluster','panel','gene_symbol'], observed=True).agg(
                        equal_animal_mean_log1p_activity=('mean_log1p_activity_per10k','mean'),
                        equal_animal_detection=('fraction_activity_detected','mean'), n_animals=('animal_id','nunique')).reset_index()
            equal.to_csv(destination / 'equal_animal_markers.tsv', sep='\t', index=False, na_rep='NA')
            save(destination / 'complete.json', {'n_cells': len(obs), 'resolution': 1.0, 'branch': branch,
                 'panel_genes': len(genes), 'zero_total_activity_cells': zeros,
                 'counts_source': 'raw integer GENCODE M25 gene-body accessibility; not RNA expression',
                 'normalization': 'log1p activity per10k using all gene-body activity counts; equal observed animal weights',
                 'aggregate_helper_sha256': policy['marker_helper_sha256'], 'unmapped_markers_are_NA': True,
                 'cell_types_assigned': False, 'exclusions_applied': False, 'final_annotation_complete': False})
        save(out / 'complete.json', {'n_cells': len(obs), 'resolution': 1.0, 'branches': list(branch_state),
                                    'new_membership_activity_aggregation_complete': True, 'final_annotations_pending': True})
    finally:
        activity.file.close()


def main(out):
    policy = json.loads((SRC / 'policy.json').read_text())
    sc.settings.n_jobs = policy['resources']['CPUs']
    save(out / 'runtime.actual.json', verify_runtime(policy))
    synthetic_fixture(out / 'runtime_fixture', policy)
    obs = read_obs_only(policy['atlas']['path'], access := [])
    need(len(obs) == policy['n_cells'] and obs.animal_id.nunique() == 20
         and obs.library_id.nunique() == 104 and obs.condition.nunique() == 5,
         'Accepted complete-study cell/animal/library/condition coverage changed')
    original_ids = obs.index.copy()
    for field in ['animal_id','library_id','condition','genotype','sex', 'initial_cluster', 'initial_cluster_uncorrected']:
        need(field in obs and not obs[field].isna().any(), 'Missing graph/biological metadata: ' + field)
    numerator = pd.to_numeric(obs.mitochondrial).to_numpy(dtype=float)
    denominator = pd.to_numeric(obs.query_names_seen).to_numpy(dtype=float)
    need((denominator > 0).all() and (numerator >= 0).all() and (numerator <= denominator).all(),
         'Original ATAC mitochondrial query-group metric invalid')
    obs['qc_pct_mt_query_groups'] = 100 * numerator / denominator
    summaries, graph_proofs = {}, {}
    for branch, spec in policy['graphs'].items():
        graph = read_graph_only(policy['atlas']['path'], spec['key'], len(obs), spec['nnz'], access)
        labels, proof = cluster_graph(graph, obs.index, policy, spec['new_cluster'])
        obs[spec['new_cluster']] = labels
        graph_proofs[branch] = {'key': spec['key'], 'nnz': int(graph.nnz), **proof}
        del graph, labels
        gc.collect()
        summaries[branch] = emit_coverage(obs, branch, spec, out)
        save(out / (branch + '_graph_complete.json'), {'branch': branch, 'resolution': 1.0, **summaries[branch],
             'graph_only_completed': True, 'raw_peak_X_read': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False})
    keys = ['initial_cluster', 'initial_cluster_uncorrected', 'initial_cluster_resolution1',
            'initial_cluster_uncorrected_resolution1', 'animal_id','library_id','condition','genotype','sex']
    obs[keys].to_csv(out / 'cell_resolution0_6_and_1_assignments.tsv.gz', sep='\t', index_label='cell_id')
    save(out / 'graph_stage_complete.json', {'resolution': 1.0, 'seed': 1729, 'n_cells': len(obs),
         'summaries': summaries, 'graphs': graph_proofs, 'accessed_peak_atlas_groups': access,
         'raw_peak_X_read': False, 'all_initial_cells_retained': True, 'original_0_6_labels_preserved': True,
         'TFIDF_LSI_Harmony_UMAP_rerun': False, 'source_atlas_modified': False, 'final_annotations_pending': True})
    markers(obs, policy, out / 'marker_review_resolution1')
    need(obs.index.equals(original_ids), 'New marker review changed cells/order')
    save(out / 'science_complete.json', {'resolution': 1.0, 'seed': 1729, 'n_cells': len(obs),
         'corrected_and_uncorrected_graphs_complete': True, 'new_107_gene_activity_summaries_complete': True,
         'raw_peak_X_read': False, 'activity_counts_read_only_in_10000_row_blocks': True,
         'source_atlas_modified': False, 'initial_diagnostic_only': True, 'final_cell_selection': False,
         'final_annotation_complete': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False})


if __name__ == '__main__':
    main(Path(sys.argv[1]))
