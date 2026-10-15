"""Validate saved Leiden1 small products and package real per-resolution adapters.

No source atlas, raw matrix, sparse graph, embedding calculation or model is read
or executed. A terminal upstream failure produces a review-needed result only.
"""
import sys
sys.dont_write_bytecode = True
import base64
from collections import Counter, defaultdict
import csv
import datetime
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import traceback
from common import SRC, identity, load, need, save, sha, stat_input, verify_source

TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL',
            'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED', 'SPECIAL_EXIT'}
FIXTURE_CHECKS = {'exact_obs_order', 'corrected_expected_disconnected_partition',
    'corrected_seed_repeat_exact', 'corrected_graph_preserved',
    'uncorrected_expected_disconnected_partition', 'uncorrected_seed_repeat_exact',
    'uncorrected_graph_preserved', 'actual_frozen_marker_aggregate_integer_sum',
    'actual_frozen_marker_aggregate_detection', 'actual_frozen_marker_aggregate_finite',
    'marker_raw_sparse_preserved', 'whitelist_never_read_X'}
NA = {'', 'NA', 'NaN', 'nan'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def rows(path, policy):
    identity(path, policy['maximum_small_file_bytes'])
    opener = gzip.open if path.name.endswith('.gz') else open
    with opener(path, 'rt', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        need(reader.fieldnames and all(reader.fieldnames) and len(reader.fieldnames) == len(set(reader.fieldnames)),
             'Missing/duplicate table column names: ' + str(path))
        for row in reader:
            need(None not in row and all(value is not None for value in row.values()), 'Ragged table row: ' + str(path))
            yield row


def integer(value, label):
    need(isinstance(value, str) and value.isdigit(), 'Nonnegative integer required: ' + label)
    return int(value)


def finite(value, label):
    result = float(value)
    need(math.isfinite(result) and result >= 0, 'Finite nonnegative value required: ' + label)
    return result


def actual_accounting(job):
    result = subprocess.run(['sacct', '-n', '-P', '-j', job,
        '--format=JobID%60,State%40,ExitCode,Start,End'], text=True, capture_output=True,
        check=True, timeout=90, stdin=subprocess.DEVNULL)
    names = ['JobID', 'State', 'ExitCode', 'Start', 'End']
    parsed = [dict(zip(names, line.strip().split('|')[:5])) for line in result.stdout.splitlines() if line.strip()]
    return {'source': 'actual_sacct', 'synthetic_only': False, 'query': job,
            'observed_utc': utc(), 'raw': result.stdout, 'rows': parsed}


def accounting_pair(snapshot, job):
    pair = []
    for selector in [job, job + '.batch']:
        matches = [row for row in snapshot['rows'] if row['JobID'] == selector]
        need(len(matches) == 1, 'Missing/duplicate exact upstream accounting: ' + selector)
        row = matches[0]
        need(row['State'].split()[0].rstrip('+') in TERMINAL and row['End'] not in ('', 'None', 'Unknown'),
             'Upstream is not actually terminal: ' + selector)
        pair.append(row)
    return pair


def all_success(pair):
    return all(row['State'] == 'COMPLETED' and row['ExitCode'] == '0:0' for row in pair)


def require_fields(value, fields, label):
    for key, expected in fields.items():
        need(key in value and type(value[key]) is type(expected) and value[key] == expected,
             label + ' field mismatch: ' + key)


def validate_receipts(producer, policy):
    need(not (producer / 'failed.json').exists(), 'Upstream has a failure receipt')
    started = load(producer / 'started.json')
    complete = load(producer / 'complete.json')
    execution = load(producer / 'execution_complete.json')
    storage = load(producer / 'storage_complete.json')
    require_fields(started, {'job_id': policy['upstream_job_id'],
        'source_manifest_sha256': policy['upstream_source_manifest_sha256'],
        'raw_peak_X_will_not_be_read': True, 'TFIDF_LSI_Harmony_UMAP_rerun': False,
        'initial_diagnostic_only': True}, 'Startup')
    need(started['inputs'] == policy['accepted_inputs'] and started['runtime_versions'] == policy['runtime_versions'] and
         started['explicit_Leiden_parameters'] == policy['leiden'], 'Startup accepted inputs/runtime/settings differ')
    controller = dict(token.split('=', 1) for token in started['controller'].split() if '=' in token)
    need(controller.get('JobId') == policy['upstream_job_id'] and controller.get('JobState') == 'RUNNING' and
         controller.get('UserId') == 'mujahid(10796)' and controller.get('Account') == policy['account'],
         'Actual upstream startup controller mapping differs')
    require_fields(complete, {'job_id': policy['upstream_job_id'], 'returncode': 0, 'resolution': 1,
        'source_manifest_sha256': policy['upstream_source_manifest_sha256'], 'n_cells': policy['n_cells'],
        'corrected_and_uncorrected_saved_graph_clustering_complete': True,
        'new_107_gene_activity_markers_complete': True, 'original_0_6_atlas_preserved': True,
        'TFIDF_LSI_Harmony_UMAP_rerun': False, 'raw_peak_X_read': False,
        'final_cell_selection': False, 'final_annotations_pending': True}, 'Completion')
    require_fields(execution, {'job_id': policy['upstream_job_id'], 'returncode': 0,
        'science_complete_sha256': sha(producer / 'science_complete.json')}, 'Execution')
    for key, size_key, inode_key in [('shared_usage', 'shared_cap_bytes', 'shared_cap_inodes'),
                                     ('own_stage', 'upstream_own_stage_bytes', 'upstream_own_stage_inodes')]:
        proof = storage[key]
        need(0 <= proof['bytes_including_child_unlinked'] <= policy[size_key] and
             0 <= proof['inodes'] <= policy[inode_key], 'Upstream storage proof exceeds fixed bound')
    runtime = load(producer / 'runtime.actual.json')
    need(runtime['versions'] == policy['runtime_versions'] and runtime['explicit_parameters'] == policy['leiden'],
         'Actual upstream runtime/settings differ')
    fixture = load(producer / 'runtime_fixture/complete.json')
    require_fields(fixture, {'status': 'passed', 'synthetic_only': True, 'cells': 12,
        'resolution': 1.0, 'seed': policy['seed'], 'study_clustering_completed': False}, 'Runtime fixture')
    need(set(fixture['checks']) == FIXTURE_CHECKS and all(value is True for value in fixture['checks'].values()),
         'Every actual runtime fixture check must pass')
    need(all(name == '/obs' or name.startswith('/obsp/') for name in fixture['accessed_input_groups']),
         'Fixture read outside approved metadata/graph groups')
    graph = load(producer / 'graph_stage_complete.json')
    require_fields(graph, {'resolution': 1.0, 'seed': policy['seed'], 'n_cells': policy['n_cells'],
        'raw_peak_X_read': False, 'all_initial_cells_retained': True, 'original_0_6_labels_preserved': True,
        'TFIDF_LSI_Harmony_UMAP_rerun': False, 'source_atlas_modified': False}, 'Graph stage')
    expected_access = ['/obs'] + ['/obsp/' + spec['key'] for spec in policy['graphs'].values()]
    need(graph['accessed_peak_atlas_groups'] == expected_access and set(graph['graphs']) == set(policy['graphs']) and
         set(graph['summaries']) == set(policy['graphs']), 'Graph read scope/branch inventory differs')
    for branch, spec in policy['graphs'].items():
        proof = graph['graphs'][branch]
        need(proof['key'] == spec['key'] and proof['nnz'] == spec['nnz'] and proof['unchanged'] is True and
             isinstance(proof['before_sha256'], str) and len(proof['before_sha256']) == 64 and
             all(char in '0123456789abcdef' for char in proof['before_sha256']) and
             proof['before_sha256'] == proof['after_sha256'], 'Saved graph preservation differs: ' + branch)
        branch_proof = load(producer / (branch + '_graph_complete.json'))
        require_fields(branch_proof, {'branch': branch, 'resolution': 1.0, 'n_cells': policy['n_cells'],
            'graph_only_completed': True, 'raw_peak_X_read': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False,
            'old_cluster_key': spec['old_cluster'], 'new_cluster_key': spec['new_cluster']}, 'Branch graph')
        need(branch_proof['n_clusters'] == graph['summaries'][branch]['n_clusters'], 'Branch cluster count differs')
    science = load(producer / 'science_complete.json')
    require_fields(science, {'resolution': 1.0, 'seed': policy['seed'], 'n_cells': policy['n_cells'],
        'corrected_and_uncorrected_graphs_complete': True, 'new_107_gene_activity_summaries_complete': True,
        'raw_peak_X_read': False, 'activity_counts_read_only_in_10000_row_blocks': True,
        'source_atlas_modified': False, 'initial_diagnostic_only': True, 'final_cell_selection': False,
        'final_annotation_complete': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False}, 'Science stage')
    markers = load(producer / 'marker_review_resolution1/complete.json')
    require_fields(markers, {'resolution': 1.0, 'n_cells': policy['n_cells'],
        'new_membership_activity_aggregation_complete': True, 'final_annotations_pending': True}, 'Marker stage')
    need(markers['branches'] == list(policy['graphs']), 'Marker branch inventory differs')
    return graph


def read_assignments(path, policy):
    ids, axis_hash, old_hash = set(), hashlib.sha256(), hashlib.sha256()
    animals = policy['initial_animal_order']; animal_codes = {animal: i for i, animal in enumerate(animals)}
    need(len(animals) == policy['n_animals'] and set(animals) == set(policy['expected_animals']), 'Animal dictionary differs')
    animal_counts, libraries, conditions = Counter(), set(), set()
    labels = {branch: [] for branch in policy['graphs']}
    counts = {branch: Counter() for branch in policy['graphs']}
    fields = ['animal_id', 'library_id', 'condition', 'genotype', 'sex']
    tables = {branch: {field: Counter() for field in fields} for branch in policy['graphs']}
    joint = {branch: Counter() for branch in policy['graphs']}
    contingency = {branch: Counter() for branch in policy['graphs']}
    metadata = {}
    n = 0
    for row in rows(path, policy):
        need(n < policy['n_cells'], 'Assignment table exceeds the fixed expected row count')
        cell = row['cell_id']
        need(cell and cell not in ids, 'Duplicate/empty assignment cell ID')
        ids.add(cell); axis_hash.update((cell + '\n').encode('utf-8'))
        animal = row['animal_id']; need(animal in animal_codes, 'Unexpected animal')
        need(row['condition'] == policy['expected_animals'][animal], 'Animal/condition differs')
        animal_prefix, age, sex, replicate = animal.rsplit('_', 3)
        genotype = policy['expected_genotype_by_animal'][animal]
        need(row['genotype'] == genotype and row['sex'] == sex, 'Animal canonical genotype/sex differs')
        current = {'id': animal, 'condition': row['condition'], 'genotype': genotype, 'sex': sex, 'age': age}
        if animal in metadata: need(metadata[animal] == current, 'Inconsistent animal attributes')
        metadata[animal] = current
        c, u = integer(row['initial_cluster'], 'old corrected'), integer(row['initial_cluster_uncorrected'], 'old uncorrected')
        need(c < 256 and u < 256 and animal_codes[animal] < 256, 'Old point attributes do not fit uint8')
        old_hash.update(bytes([c, u, animal_codes[animal]]))
        animal_counts[animal] += 1; libraries.add(row['library_id']); conditions.add(row['condition'])
        need(bool(row['library_id']), 'Empty library')
        for branch, spec in policy['graphs'].items():
            label = row[spec['new_cluster']]
            need(bool(label) and label.isdigit(), 'Invalid actual new cluster label')
            labels[branch].append(label); counts[branch][label, animal] += 1
            for field in fields: tables[branch][field][label, row[field]] += 1
            joint[branch][label, animal, row['library_id'], row['condition']] += 1
            contingency[branch][row[spec['old_cluster']], label] += 1
        n += 1
    need(n == policy['n_cells'] and axis_hash.hexdigest() == policy['ordered_cell_ids_sha256'],
         'Exact ordered accepted cell axis differs')
    need(old_hash.hexdigest() == policy['initial_point_attribute_bytes_sha256'],
         'Old corrected/uncorrected labels or animal axis differ from accepted exported attributes')
    need(len(libraries) == policy['n_libraries'] and len(conditions) == policy['n_conditions'] and
         len(animal_counts) == policy['n_animals'], 'Complete-study biological/library coverage differs')
    for animal in animals: metadata[animal]['n_initial_cells'] = animal_counts[animal]
    return {'labels': labels, 'counts': counts, 'animals': [metadata[a] for a in animals],
            'table_counts': tables, 'joint_counts': joint, 'contingency': contingency,
            'n_cells': n, 'axis_sha256': axis_hash.hexdigest(), 'old_attributes_sha256': old_hash.hexdigest()}


def validate_coverage(producer, branch, axis, policy):
    count = axis['counts'][branch]
    prefix = branch + '_resolution1'
    by_cluster = Counter()
    for (cluster, animal), n in count.items(): by_cluster[cluster] += n
    summary = list(rows(producer / (prefix + '_cluster_summary.tsv'), policy))
    seen = set()
    for row in summary:
        cluster = row[policy['graphs'][branch]['new_cluster']]
        need(cluster not in seen and integer(row['n_cells'], 'coverage n') == by_cluster[cluster], 'Cluster summary size differs')
        need(integer(row['n_animals'], 'coverage animals') == sum(c == cluster for c, a in count), 'Cluster animal count differs')
        for field, column in [('library_id', 'n_libraries'), ('condition', 'n_conditions')]:
            expected = sum(c == cluster for c, category in axis['table_counts'][branch][field])
            need(integer(row[column], column) == expected, 'Cluster ' + field + ' coverage differs')
        seen.add(cluster)
    need(seen == set(by_cluster), 'Cluster summary inventory differs')
    for field, expected in axis['table_counts'][branch].items():
        table = list(rows(producer / (prefix + '_by_' + field + '.tsv'), policy))
        need(len(table) == len(by_cluster), field + ' crosstab cluster count differs')
        categories, seen = {category for cluster, category in expected}, set()
        for row in table:
            cluster = row[policy['graphs'][branch]['new_cluster']]
            need(cluster not in seen and cluster in by_cluster, field + ' crosstab cluster differs')
            need(set(row) == {policy['graphs'][branch]['new_cluster'], *categories}, 'Crosstab category axis differs')
            seen.add(cluster)
            for category in categories:
                need(integer(row[category], field + ' crosstab') == expected.get((cluster, category), 0), 'Crosstab size differs')
    joint = {}
    for row in rows(producer / (prefix + '_animal_library_condition_coverage.tsv'), policy):
        key = row[policy['graphs'][branch]['new_cluster']], row['animal_id'], row['library_id'], row['condition']
        need(key not in joint, 'Duplicate joint coverage row')
        joint[key] = integer(row['n_cells'], 'joint coverage count')
    need(joint == dict(axis['joint_counts'][branch]), 'Animal/library/condition joint counts differ')
    expected = axis['contingency'][branch]
    old_labels, new_labels, seen = {old for old, new in expected}, set(by_cluster), set()
    for row in rows(producer / (branch + '_resolution0_6_vs_1_contingency.tsv'), policy):
        old = row[policy['graphs'][branch]['old_cluster']]
        need(old in old_labels and old not in seen and
             set(row) == {policy['graphs'][branch]['old_cluster'], *new_labels}, 'Old/new contingency label axis differs')
        seen.add(old)
        for new in new_labels:
            need(integer(row[new], 'old/new contingency') == expected.get((old, new), 0), 'Old/new contingency count differs')
    need(seen == old_labels, 'Old/new contingency coverage differs')
    return by_cluster


def validate_markers(directory, branch, count, panels, policy):
    genes = list(dict.fromkeys(gene for values in panels.values() for gene in values))
    need(len(genes) == policy['n_marker_genes'], 'Expected 107-gene diagnostic panel differs')
    audit, unique, full, duplicate_rows = {}, {}, set(), 0
    for row in rows(directory / 'symbol_audit.tsv', policy):
        gene = row['gene_symbol']; need(gene in genes and gene not in audit, 'Symbol audit duplicate/unexpected gene')
        n = integer(row['n_features'], 'mapped feature count')
        need(row['present'] in ['True', 'False'] and (row['present'] == 'True') == (n > 0), 'Mapping truth/feature count differs')
        audit[gene] = n > 0
    need(set(audit) == set(genes), 'Symbol audit gene inventory differs')
    for row in rows(directory / 'markers_by_cluster_animal.tsv', policy):
        cluster, animal, panel, gene = row['initial_cluster'], row['animal_id'], row['panel'], row['gene_symbol']
        need(panel in panels and gene in panels[panel] and (cluster, animal) in count, 'Marker membership/panel differs')
        n = integer(row['n_cells'], 'marker cell count'); need(n == count[cluster, animal] and n > 0, 'Marker group size differs')
        key = cluster, animal, gene
        if audit[gene]:
            raw = integer(row['raw_integer_activity_sum'], 'raw activity')
            detection = finite(row['fraction_activity_detected'], 'detection')
            normalized = finite(row['mean_log1p_activity_per10k'], 'normalized activity')
            need(detection <= 1 and abs(detection * n - round(detection * n)) < 1e-5 and
                 round(detection * n) <= raw, 'Detection/raw integer support differs')
            need((raw == 0 and detection == 0 and normalized == 0) or
                 (raw > 0 and detection > 0 and normalized > 0), 'Positive/zero raw-detection-normalized support differs')
            value = [n, raw, detection, normalized]
        else:
            need(all(row[field] in NA for field in ['raw_integer_activity_sum', 'fraction_activity_detected',
                                                   'mean_log1p_activity_per10k']), 'Unmapped activity must be explicit NA')
            value = [n, None, None, None]
        if key in unique:
            need(unique[key] == value, 'Conflicting duplicate panel marker values')
            duplicate_rows += 1
        unique[key] = value
        full_key = cluster, animal, panel, gene
        need(full_key not in full, 'Duplicate complete panel/group/gene row')
        full.add(full_key)
    expected = {(cluster, animal, panel, gene) for cluster, animal in count for panel, values in panels.items() for gene in values}
    need(full == expected and len(unique) == len(count) * len(genes), 'Fresh marker group/panel coverage differs')
    equal_seen = set()
    for row in rows(directory / 'equal_animal_markers.tsv', policy):
        cluster, panel, gene = row['initial_cluster'], row['panel'], row['gene_symbol']
        key = cluster, panel, gene
        need(panel in panels and gene in panels[panel] and key not in equal_seen, 'Equal-animal panel/duplicate differs')
        vals = [unique[c, a, gene] for c, a in count if c == cluster]
        need(bool(vals) and integer(row['n_animals'], 'equal animal n') == len(vals), 'Equal-animal coverage differs')
        if audit[gene]:
            need(abs(sum(v[2] for v in vals) / len(vals) - finite(row['equal_animal_detection'], 'equal detection')) < 1e-12 and
                 abs(sum(v[3] for v in vals) / len(vals) - finite(row['equal_animal_mean_log1p_activity'], 'equal normalized')) < 1e-12,
                 'Fresh equal-animal summary parity failed')
        else:
            need(row['equal_animal_detection'] in NA and row['equal_animal_mean_log1p_activity'] in NA,
                 'Unmapped equal-animal summary must be NA')
        equal_seen.add(key)
    need(equal_seen == {(cluster, panel, gene) for cluster in {c for c, a in count}
                       for panel, values in panels.items() for gene in values}, 'Equal marker inventory differs')
    complete = load(directory / 'complete.json')
    require_fields(complete, {'n_cells': policy['n_cells'], 'resolution': 1.0, 'branch': branch,
        'panel_genes': policy['n_marker_genes'], 'aggregate_helper_sha256': policy['marker_helper_sha256'],
        'unmapped_markers_are_NA': True, 'cell_types_assigned': False, 'exclusions_applied': False,
        'final_annotation_complete': False}, 'Branch marker completion')
    need(complete['counts_source'] == 'raw integer GENCODE M25 gene-body accessibility; not RNA expression' and
         complete['normalization'] == 'log1p activity per10k using all gene-body activity counts; equal observed animal weights',
         'Marker activity units/denominator differ')
    return {'genes': genes, 'mapped': audit, 'unique': unique, 'duplicate_panel_rows_collapsed': duplicate_rows}


def copy_product(source, target, inventory, policy):
    before = identity(source, policy['maximum_small_file_bytes'])
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    need(sha(target) == before['sha256'] and identity(source, policy['maximum_small_file_bytes']) == before,
         'Producer product changed during package transfer')
    inventory.append({'packaged_path': str(target), 'source_identity': before,
                      'copied_bytes': target.stat().st_size, 'sha256': sha(target)})


def make_adapters(staging, axis, marker_data, panels, cluster_counts, policy):
    inventory, labels_json = {}, {}
    for branch, values in axis['labels'].items():
        dictionary = sorted(set(values), key=int)
        need(0 < len(dictionary) <= 65535, 'Label dictionary does not fit declared uint16')
        codes = {value: i for i, value in enumerate(dictionary)}
        blob = b''.join(struct.pack('<H', codes[value]) for value in values)
        file = staging / (branch + '_labels.u16le'); file.write_bytes(blob)
        labels_json[branch] = {'n': axis['n_cells'], 'dtype': 'uint16-little-endian', 'labels': dictionary,
            'base64': base64.b64encode(blob).decode('ascii'), 'derived_bytes_sha256': hashlib.sha256(blob).hexdigest()}
        data = marker_data[branch]
        records = [[cluster, animal, gene, *value] for (cluster, animal, gene), value in
                   sorted(data['unique'].items(), key=lambda x: (int(x[0][0]), x[0][1], x[0][2]))]
        adapter = {'schema_version': '1.0', 'dataset_id': 'ATAC_resolution1_7470007_' + branch,
            'job_id': '7470007', 'resolution': 1.0, 'partition_graph': branch,
            'provisional': True, 'n_cells': axis['n_cells'], 'final_qc_available': False,
            'final_labels_available': False, 'coordinates_reused_from': 'ATAC_initial_7466270',
            'coordinate_recomputation': False, 'ordered_cell_ids_sha256': axis['axis_sha256'],
            'initial_point_attributes_sha256': axis['old_attributes_sha256'],
            'animals': axis['animals'], 'clusters': [{'id': label, 'n': cluster_counts[branch][label],
                'candidate': 'Unreviewed resolution-1 cluster', 'status': 'provisional; independent annotation pending'}
                for label in dictionary],
            'genes': [{'symbol': gene, 'mapped': data['mapped'][gene]} for gene in data['genes']],
            'panels': panels, 'record_columns': ['cluster', 'animal', 'gene', 'n_cells',
                'raw_integer_activity_sum', 'fraction_activity_detected', 'mean_log1p_activity_per10k'],
            'records': records, 'activity_units': 'GENCODE M25 gene-body accessibility; not RNA expression',
            'marker_scope': 'selected 107-gene diagnostic panel; not genome-wide differential top markers',
            'normalization': 'log1p activity per10k using all gene-body activity counts; equal-animal summaries',
            'display_label_scope': 'dataset+resolution+partition_graph; do not inherit old numeric cluster labels'}
        jsonfile = staging / (branch + '_activity_adapter.json'); save(jsonfile, adapter)
        jsfile = staging / (branch + '_activity_adapter.js')
        jsfile.write_text('window.ATLAS_RESOLUTION_DATASETS=window.ATLAS_RESOLUTION_DATASETS||{};\n'
            + 'window.ATLAS_RESOLUTION_DATASETS[' + json.dumps(adapter['dataset_id']) + ']='
            + json.dumps(adapter, separators=(',', ':'), allow_nan=False) + ';\n')
        inventory[branch] = {'label_dictionary': dictionary, 'n_clusters': len(dictionary),
            'n_unique_marker_records': len(records), 'unmapped_genes': sum(not x for x in data['mapped'].values()),
            'duplicate_panel_rows_collapsed': data['duplicate_panel_rows_collapsed']}
    (staging / 'resolution1_labels.js').write_text('window.ATLAS_RESOLUTION1_LABELS='
        + json.dumps({'n_cells': axis['n_cells'], 'ordered_cell_ids_sha256': axis['axis_sha256'],
            'branches': labels_json}, separators=(',', ':')) + ';\n')
    return inventory


def review_needed(out, producer, policy, package_job, accounting, reason):
    partials = []
    for source in sorted(producer.glob('corrected*')):
        if source.is_file() and not source.is_symlink() and source.suffix in ['.json', '.tsv']:
            copy_product(source, out / 'review_partials' / source.name, partials, policy)
    result = {'utc': utc(), 'status': 'review_needed_no_package_published',
        'upstream_job_id': policy['upstream_job_id'], 'package_job_id': package_job,
        'reason': reason, 'actual_accounting': accounting, 'corrected_partials_preserved': partials,
        'original_producer_products_modified': False, 'upstream_job_rerun': False,
        'package_published': False, 'normalization_ready': False, 'final_QC_or_annotation_adopted': False,
        'HTML_resolution1_enabled': False}
    save(out / 'review_needed.json', result); save(out / 'stage_result.json', result)


def main():
    need(len(sys.argv) == 3, 'Require NEW_PACKAGE_JOB_DIR and actual package job ID')
    out, package_job = Path(sys.argv[1]), sys.argv[2]
    policy = load(SRC / 'package_policy.json')
    need(policy['upstream_job_id'] == '7470007' and policy['n_cells'] == 456472 and
         policy['n_marker_genes'] == 107 and policy['resolution'] == 1.0 and
         policy['normalization_ready'] is False and policy['final_QC_or_annotation_adopted'] is False,
         'Fixed actual producer/scientific scope changed')
    need(package_job.isdigit() and package_job == os.environ['SLURM_JOB_ID'], 'Actual package identity differs')
    source_sha = verify_source(SRC)
    root = Path(policy['root'])
    producer_source = root / 'pre_processed_ATAC/analysis_source' / policy['upstream_source_version']
    producer = root / 'pre_processed_ATAC/analysis_runs' / policy['upstream_source_version'] / ('job-' + policy['upstream_job_id'])
    need(producer.is_dir() and not producer.is_symlink(), 'Producer output directory absent/symlink')
    accounting = actual_accounting(policy['upstream_job_id'])
    save(out / 'upstream_actual_accounting.json', accounting)
    try:
        pair = accounting_pair(accounting, policy['upstream_job_id'])
        if not all_success(pair):
            review_needed(out, producer, policy, package_job, accounting,
                          'Actual upstream whole/batch did not both complete0:0; no automatic rerun')
            return
        verify_source(producer_source, policy['upstream_source_manifest_sha256'], policy['upstream_source_members'])
        verify_source(root / 'pre_processed_ATAC/analysis_source' / policy['accepted_initial_source_version'],
                      policy['accepted_initial_source_manifest_sha256'])
        for record in policy['accepted_inputs']: stat_input(record)
        graph = validate_receipts(producer, policy)
        need(sha(SRC / 'marker_panels.json') == policy['marker_panels_sha256'], 'Exact marker panel source differs')
        panels = load(SRC / 'marker_panels.json')
        axis = read_assignments(producer / 'cell_resolution0_6_and_1_assignments.tsv.gz', policy)
        marker_data, coverage = {}, {}
        for branch in policy['graphs']:
            coverage[branch] = validate_coverage(producer, branch, axis, policy)
            need(len(coverage[branch]) == graph['summaries'][branch]['n_clusters'], 'Actual assignment/graph cluster counts differ')
            marker_data[branch] = validate_markers(producer / 'marker_review_resolution1' / branch,
                                                  branch, axis['counts'][branch], panels, policy)
        need(marker_data['corrected']['mapped'] == marker_data['uncorrected']['mapped'], 'Branch feature mapping differs')
        staging = out / 'validated_products'; staging.mkdir(exist_ok=False)
        inventory = []
        source_names = ['started.json', 'complete.json', 'execution_complete.json', 'storage_complete.json',
            'runtime.actual.json', 'runtime_fixture/complete.json', 'graph_stage_complete.json',
            'science_complete.json', 'corrected_graph_complete.json', 'uncorrected_graph_complete.json',
            'cell_resolution0_6_and_1_assignments.tsv.gz', 'marker_review_resolution1/complete.json']
        for branch in policy['graphs']:
            source_names.extend('marker_review_resolution1/' + branch + '/' + name for name in
                                ['complete.json', 'markers_by_cluster_animal.tsv', 'equal_animal_markers.tsv', 'symbol_audit.tsv'])
            source_names.extend(branch + '_resolution1' + suffix for suffix in
                ['_cluster_summary.tsv', '_by_animal_id.tsv', '_by_library_id.tsv', '_by_condition.tsv',
                 '_by_genotype.tsv', '_by_sex.tsv', '_animal_library_condition_coverage.tsv',
                 '_QC_quantiles.tsv', '_animal_QC_quantiles.tsv'])
            source_names.append(branch + '_resolution0_6_vs_1_contingency.tsv')
        for name in source_names: copy_product(producer / name, staging / 'producer_products' / name, inventory, policy)
        adapters = make_adapters(staging, axis, marker_data, panels, coverage, policy)
        for record in policy['accepted_inputs']: stat_input(record)
        verify_source(producer_source, policy['upstream_source_manifest_sha256'], policy['upstream_source_members'])
        need(not (producer / 'failed.json').exists(), 'Producer acquired a failure receipt during packaging')
        output_files = {str(path.relative_to(staging)): identity(path) for path in sorted(staging.rglob('*')) if path.is_file()}
        need(sum(value['bytes'] for value in output_files.values()) <= policy['maximum_package_bytes'], 'Finite package byte bound exceeded')
        manifest = {'utc': utc(), 'status': 'validated_initial_resolution1_package', 'upstream_job_id': '7470007',
            'package_job_id': package_job, 'package_source_manifest_sha256': source_sha,
            'upstream_source_manifest_sha256': policy['upstream_source_manifest_sha256'],
            'actual_successful_whole_batch': pair, 'upstream_accounting_sha256': sha(out / 'upstream_actual_accounting.json'),
            'n_cells': axis['n_cells'], 'n_animals': policy['n_animals'], 'n_libraries': policy['n_libraries'],
            'ordered_cell_ids_sha256': axis['axis_sha256'], 'initial_point_attribute_bytes_sha256': axis['old_attributes_sha256'],
            'graphs': graph['graphs'], 'adapters': adapters, 'producer_products': inventory, 'files': output_files,
            'coordinate_source': 'Existing accepted real job7466270 Harmony/uncorrected UMAP coordinate adapters; exact cell axis matched',
            'coordinates_recomputed': False, 'raw_matrix_or_graph_read': False, 'new_clustering_executed': False,
            'fresh_resolution_specific_markers_validated': True, 'diagnostic_panel_only': True,
            'cell_types_automatically_assigned': False, 'normalization_ready': False,
            'final_QC_or_annotation_adopted': False, 'HTML_resolution1_enabled': False,
            'package_job_terminal_accounting_checked': False,
            'next': 'Accept package job actual whole+batch/source/storage receipts and file hashes, then download/import on Mac. Final QC and independent annotation remain separate.'}
        save(out / 'validated_package_manifest.json', manifest)
        save(out / 'stage_result.json', {'utc': utc(), 'status': manifest['status'], 'upstream_job_id': '7470007',
            'package_job_id': package_job, 'package_published': True,
            'validated_manifest_sha256': sha(out / 'validated_package_manifest.json'),
            'normalization_ready': False, 'final_QC_or_annotation_adopted': False, 'HTML_resolution1_enabled': False})
    except Exception as error:
        review_needed(out, producer, policy, package_job, accounting,
                      {'validation_error': repr(error), 'traceback': traceback.format_exc()})


if __name__ == '__main__':
    main()
