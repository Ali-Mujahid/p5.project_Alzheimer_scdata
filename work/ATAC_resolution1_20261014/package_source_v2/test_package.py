"""Generated-only package contract regressions; never reads study products."""
import sys
sys.dont_write_bytecode = True
import copy
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from common import load, save, sha
import package_results as p


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic_Leiden_package_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prod = self.root / 'synthetic_producer'; self.prod.mkdir()
        self.policy = copy.deepcopy(load(Path(__file__).parent / 'package_policy.json'))
        self.animals = ['WT_3mo_female_1', '5xFAD_3mo_male_2']
        self.policy.update(n_cells=4, n_animals=2, n_libraries=2, n_conditions=2,
            initial_animal_order=self.animals,
            expected_animals={a: '_'.join(a.rsplit('_', 2)[:1]) for a in self.animals})
        self.policy['expected_animals'] = {'WT_3mo_female_1': 'WT_3mo', '5xFAD_3mo_male_2': '5xFAD_3mo'}
        self.policy['expected_genotype_by_animal'] = {'WT_3mo_female_1': 'WT', '5xFAD_3mo_male_2': '5xFAD'}
        self.genes = ['SyntheticGene%03d' % i for i in range(107)]
        self.panels = {'generated_panel': self.genes, 'generated_overlap': self.genes[:2]}
        self.assign = []
        for i in range(4):
            animal = self.animals[i % 2]; genotype, age, sex, rep = animal.rsplit('_', 3)
            self.assign.append({'cell_id': 'synthetic_cell_%02d' % i, 'initial_cluster': str(i // 2),
                'initial_cluster_uncorrected': str(i % 2), 'initial_cluster_resolution1': str(i // 2),
                'initial_cluster_uncorrected_resolution1': str(i % 2), 'animal_id': animal,
                'library_id': 'synthetic_library_' + str(i % 2), 'condition': genotype + '_' + age,
                'genotype': genotype, 'sex': sex})
        self.assignment_path = self.prod / 'cell_resolution0_6_and_1_assignments.tsv.gz'
        self.write_assignments()
        self.policy['ordered_cell_ids_sha256'] = hashlib.sha256(''.join(r['cell_id'] + '\n' for r in self.assign).encode()).hexdigest()
        self.policy['initial_point_attribute_bytes_sha256'] = hashlib.sha256(bytes(
            x for r in self.assign for x in [int(r['initial_cluster']), int(r['initial_cluster_uncorrected']), self.animals.index(r['animal_id'])])).hexdigest()
        self.axis = p.read_assignments(self.assignment_path, self.policy)
        self.make_receipts()
        for branch in self.policy['graphs']:
            self.make_coverage(branch)
            self.make_markers(branch)

    def write_table(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]), delimiter='\t')
            writer.writeheader(); writer.writerows(records)

    def write_assignments(self):
        with gzip.open(self.assignment_path, 'wt', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.assign[0]), delimiter='\t')
            writer.writeheader(); writer.writerows(self.assign)

    def edit_json(self, name, edit):
        file = self.prod / name; value = load(file); edit(value); save(file, value)

    def edit_table(self, path, edit):
        with path.open() as handle: values = list(csv.DictReader(handle, delimiter='\t'))
        edit(values); self.write_table(path, values)

    def make_receipts(self):
        job = self.policy['upstream_job_id']; n = self.policy['n_cells']
        save(self.prod / 'started.json', {'job_id': job,
            'source_manifest_sha256': self.policy['upstream_source_manifest_sha256'],
            'raw_peak_X_will_not_be_read': True, 'TFIDF_LSI_Harmony_UMAP_rerun': False, 'initial_diagnostic_only': True,
            'inputs': self.policy['accepted_inputs'], 'runtime_versions': self.policy['runtime_versions'],
            'explicit_Leiden_parameters': self.policy['leiden'],
            'controller': 'JobId=' + job + ' JobState=RUNNING UserId=mujahid(10796) Account=molecular_neurosciences'})
        save(self.prod / 'complete.json', {'job_id': job, 'returncode': 0, 'resolution': 1,
            'source_manifest_sha256': self.policy['upstream_source_manifest_sha256'], 'n_cells': n,
            'corrected_and_uncorrected_saved_graph_clustering_complete': True,
            'new_107_gene_activity_markers_complete': True, 'original_0_6_atlas_preserved': True,
            'TFIDF_LSI_Harmony_UMAP_rerun': False, 'raw_peak_X_read': False,
            'final_cell_selection': False, 'final_annotations_pending': True})
        save(self.prod / 'storage_complete.json', {'shared_usage': {'bytes_including_child_unlinked': 1000, 'inodes': 10},
            'own_stage': {'bytes_including_child_unlinked': 1000, 'inodes': 10}})
        save(self.prod / 'runtime.actual.json', {'versions': self.policy['runtime_versions'], 'explicit_parameters': self.policy['leiden']})
        (self.prod / 'runtime_fixture').mkdir()
        save(self.prod / 'runtime_fixture/complete.json', {'status': 'passed', 'synthetic_only': True, 'cells': 12,
            'resolution': 1.0, 'seed': self.policy['seed'], 'study_clustering_completed': False,
            'checks': dict.fromkeys(p.FIXTURE_CHECKS, True), 'accessed_input_groups': ['/obs', '/obsp/synthetic']})
        graph = {'resolution': 1.0, 'seed': self.policy['seed'], 'n_cells': n, 'raw_peak_X_read': False,
            'all_initial_cells_retained': True, 'original_0_6_labels_preserved': True,
            'TFIDF_LSI_Harmony_UMAP_rerun': False, 'source_atlas_modified': False,
            'accessed_peak_atlas_groups': ['/obs'] + ['/obsp/' + spec['key'] for spec in self.policy['graphs'].values()],
            'graphs': {}, 'summaries': {}}
        for branch, spec in self.policy['graphs'].items():
            graph['graphs'][branch] = {'key': spec['key'], 'nnz': spec['nnz'], 'unchanged': True,
                'before_sha256': 'a' * 64, 'after_sha256': 'a' * 64}
            graph['summaries'][branch] = {'n_clusters': 2}
            save(self.prod / (branch + '_graph_complete.json'), {'branch': branch, 'resolution': 1.0, 'n_cells': n,
                'graph_only_completed': True, 'raw_peak_X_read': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False,
                'old_cluster_key': spec['old_cluster'], 'new_cluster_key': spec['new_cluster'], 'n_clusters': 2})
        save(self.prod / 'graph_stage_complete.json', graph)
        save(self.prod / 'science_complete.json', {'resolution': 1.0, 'seed': self.policy['seed'], 'n_cells': n,
            'corrected_and_uncorrected_graphs_complete': True, 'new_107_gene_activity_summaries_complete': True,
            'raw_peak_X_read': False, 'activity_counts_read_only_in_10000_row_blocks': True,
            'source_atlas_modified': False, 'initial_diagnostic_only': True, 'final_cell_selection': False,
            'final_annotation_complete': False, 'TFIDF_LSI_Harmony_UMAP_rerun': False})
        save(self.prod / 'execution_complete.json', {'job_id': job, 'returncode': 0,
            'science_complete_sha256': sha(self.prod / 'science_complete.json')})
        (self.prod / 'marker_review_resolution1').mkdir()
        save(self.prod / 'marker_review_resolution1/complete.json', {'resolution': 1.0, 'n_cells': n,
            'new_membership_activity_aggregation_complete': True, 'final_annotations_pending': True,
            'branches': list(self.policy['graphs'])})

    def make_coverage(self, branch):
        count = self.axis['counts'][branch]; key = self.policy['graphs'][branch]['new_cluster']
        clusters = sorted({c for c, a in count})
        summary = [{key: c, 'n_cells': sum(n for (label, a), n in count.items() if label == c),
            'n_animals': sum(label == c for label, a in count),
            'n_libraries': sum(label == c for label, category in self.axis['table_counts'][branch]['library_id']),
            'n_conditions': sum(label == c for label, category in self.axis['table_counts'][branch]['condition'])} for c in clusters]
        self.write_table(self.prod / (branch + '_resolution1_cluster_summary.tsv'), summary)
        for field, counter in self.axis['table_counts'][branch].items():
            categories = sorted({category for cluster, category in counter})
            self.write_table(self.prod / (branch + '_resolution1_by_' + field + '.tsv'),
                [{key: c, **{category: counter.get((c, category), 0) for category in categories}} for c in clusters])
        self.write_table(self.prod / (branch + '_resolution1_animal_library_condition_coverage.tsv'),
            [{key: c, 'animal_id': a, 'library_id': library, 'condition': condition, 'n_cells': n}
             for (c, a, library, condition), n in self.axis['joint_counts'][branch].items()])
        old_key = self.policy['graphs'][branch]['old_cluster']; counter = self.axis['contingency'][branch]
        self.write_table(self.prod / (branch + '_resolution0_6_vs_1_contingency.tsv'),
            [{old_key: old, **{new: counter.get((old, new), 0) for new in clusters}}
             for old in sorted({old for old, new in counter})])

    def make_markers(self, branch):
        directory = self.prod / 'marker_review_resolution1' / branch; directory.mkdir()
        count = self.axis['counts'][branch]
        self.write_table(directory / 'symbol_audit.tsv', [{'gene_symbol': gene, 'n_features': int(i < 106),
            'present': i < 106} for i, gene in enumerate(self.genes)])
        markers, equal = [], []
        for (cluster, animal), n in count.items():
            for panel, genes in self.panels.items():
                for gene in genes:
                    j = self.genes.index(gene); present = j < 106
                    markers.append({'initial_cluster': cluster, 'animal_id': animal, 'n_cells': n,
                        'panel': panel, 'gene_symbol': gene, 'raw_integer_activity_sum': (j + 1) * n if present else 'NA',
                        'fraction_activity_detected': 1.0 if present else 'NA',
                        'mean_log1p_activity_per10k': math.log1p(j + 1) if present else 'NA'})
        for cluster in sorted({c for c, a in count}):
            for panel, genes in self.panels.items():
                for gene in genes:
                    j = self.genes.index(gene); present = j < 106
                    equal.append({'initial_cluster': cluster, 'panel': panel, 'gene_symbol': gene,
                        'equal_animal_mean_log1p_activity': math.log1p(j + 1) if present else 'NA',
                        'equal_animal_detection': 1.0 if present else 'NA',
                        'n_animals': sum(c == cluster for c, a in count)})
        self.write_table(directory / 'markers_by_cluster_animal.tsv', markers)
        self.write_table(directory / 'equal_animal_markers.tsv', equal)
        save(directory / 'complete.json', {'n_cells': 4, 'resolution': 1.0, 'branch': branch, 'panel_genes': 107,
            'aggregate_helper_sha256': self.policy['marker_helper_sha256'], 'unmapped_markers_are_NA': True,
            'cell_types_assigned': False, 'exclusions_applied': False, 'final_annotation_complete': False,
            'counts_source': 'raw integer GENCODE M25 gene-body accessibility; not RNA expression',
            'normalization': 'log1p activity per10k using all gene-body activity counts; equal observed animal weights'})

    def check_markers(self, branch='corrected'):
        return p.validate_markers(self.prod / 'marker_review_resolution1' / branch,
            branch, self.axis['counts'][branch], self.panels, self.policy)

    def rejected(self, callback):
        with self.assertRaises((RuntimeError, ValueError, KeyError)):
            callback()

    def test_valid_both_axes_and_fresh_markers(self):
        p.validate_receipts(self.prod, self.policy)
        for branch in self.policy['graphs']:
            self.assertEqual(sum(p.validate_coverage(self.prod, branch, self.axis, self.policy).values()), 4)
            self.assertEqual(len(self.check_markers(branch)['genes']), 107)

    def test_missing_batch_accounting_rejected(self):
        self.rejected(lambda: p.accounting_pair({'rows': [{'JobID': 'x'}]}, 'x'))

    def test_duplicate_accounting_rejected(self):
        row = {'JobID': 'x', 'State': 'COMPLETED', 'ExitCode': '0:0', 'End': '2026-01-01'}
        self.rejected(lambda: p.accounting_pair({'rows': [row, row]}, 'x'))

    def test_failed_and_timeout_never_count_as_success(self):
        for state in ['FAILED', 'TIMEOUT']:
            pair = [{'JobID': x, 'State': state, 'ExitCode': '1:0', 'End': '2026-01-01'} for x in ['x', 'x.batch']]
            self.assertFalse(p.all_success(p.accounting_pair({'rows': pair}, 'x')))

    def test_running_accounting_rejected(self):
        pair = [{'JobID': x, 'State': 'RUNNING', 'ExitCode': '0:0', 'End': 'Unknown'} for x in ['x', 'x.batch']]
        self.rejected(lambda: p.accounting_pair({'rows': pair}, 'x'))

    def test_failed_receipt_rejected_even_with_success_other_receipts(self):
        save(self.prod / 'failed.json', {'synthetic_only': True})
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_wrong_source_receipt_rejected(self):
        self.edit_json('complete.json', lambda x: x.update(source_manifest_sha256='0' * 64))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_changed_science_without_execution_hash_rebind_rejected(self):
        file = self.prod / 'science_complete.json'; file.write_text(file.read_text() + ' ')
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_false_actual_fixture_rejected(self):
        self.edit_json('runtime_fixture/complete.json', lambda x: x['checks'].update(exact_obs_order=False))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_truthy_fixture_string_rejected(self):
        self.edit_json('runtime_fixture/complete.json', lambda x: x['checks'].update(exact_obs_order='true'))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_graph_mutation_rejected(self):
        self.edit_json('graph_stage_complete.json', lambda x: x['graphs']['uncorrected'].update(after_sha256='b' * 64))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_raw_X_read_claim_rejected(self):
        self.edit_json('graph_stage_complete.json', lambda x: x.update(accessed_peak_atlas_groups=['/obs', '/X']))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_duplicate_cell_rejected(self):
        self.assign[-1]['cell_id'] = self.assign[0]['cell_id']; self.write_assignments()
        self.rejected(lambda: p.read_assignments(self.assignment_path, self.policy))

    def test_reordered_axis_rejected(self):
        self.assign.reverse(); self.write_assignments()
        self.rejected(lambda: p.read_assignments(self.assignment_path, self.policy))

    def test_changed_old_label_rejected(self):
        self.assign[0]['initial_cluster'] = '9'; self.write_assignments()
        self.rejected(lambda: p.read_assignments(self.assignment_path, self.policy))

    def test_wrong_animal_condition_rejected(self):
        self.assign[0]['condition'] = 'wrong'; self.write_assignments()
        self.rejected(lambda: p.read_assignments(self.assignment_path, self.policy))

    def set_actual_APOE4_genotype(self):
        old, new = '5xFAD_3mo_male_2', 'APOE4_TREM2_3mo_male_2'
        self.policy['initial_animal_order'][1] = new
        self.policy['expected_animals'].pop(old); self.policy['expected_animals'][new] = 'APOE4_TREM2_3mo'
        self.policy['expected_genotype_by_animal'].pop(old); self.policy['expected_genotype_by_animal'][new] = 'APOE4/TREM2'
        for row in self.assign:
            if row['animal_id'] == old:
                row.update(animal_id=new, condition='APOE4_TREM2_3mo', genotype='APOE4/TREM2')
        self.write_assignments()

    def test_source_canonical_APOE4_slash_genotype_is_preserved(self):
        self.set_actual_APOE4_genotype()
        axis = p.read_assignments(self.assignment_path, self.policy)
        self.assertEqual(axis['animals'][1]['genotype'], 'APOE4/TREM2')

    def test_animal_prefix_cannot_replace_canonical_genotype(self):
        self.set_actual_APOE4_genotype()
        self.assign[1]['genotype'] = 'APOE4_TREM2'; self.write_assignments()
        self.rejected(lambda: p.read_assignments(self.assignment_path, self.policy))

    def test_wrong_marker_size_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: x[0].update(n_cells='99')); self.rejected(self.check_markers)

    def test_missing_marker_membership_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: x.pop()); self.rejected(self.check_markers)

    def test_noninteger_activity_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: x[0].update(raw_integer_activity_sum='1.5')); self.rejected(self.check_markers)

    def test_negative_activity_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: x[0].update(raw_integer_activity_sum='-1')); self.rejected(self.check_markers)

    def test_infinite_normalized_activity_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: x[0].update(mean_log1p_activity_per10k='inf')); self.rejected(self.check_markers)

    def test_unmapped_zero_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: next(r for r in x if r['gene_symbol'] == self.genes[-1]).update(raw_integer_activity_sum='0'))
        self.rejected(self.check_markers)

    def test_conflicting_panel_duplicate_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/markers_by_cluster_animal.tsv'
        self.edit_table(file, lambda x: next(r for r in x if r['panel'] == 'generated_overlap').update(raw_integer_activity_sum='123'))
        self.rejected(self.check_markers)

    def test_wrong_equal_animal_mean_rejected(self):
        file = self.prod / 'marker_review_resolution1/corrected/equal_animal_markers.tsv'
        self.edit_table(file, lambda x: x[0].update(equal_animal_mean_log1p_activity='123')); self.rejected(self.check_markers)

    def test_old_resolution_marker_receipt_rejected(self):
        self.edit_json('marker_review_resolution1/corrected/complete.json', lambda x: x.update(resolution=0.6))
        self.rejected(self.check_markers)

    def test_wrong_coverage_rejected(self):
        self.edit_table(self.prod / 'corrected_resolution1_by_animal_id.tsv', lambda x: x[0].update({self.animals[0]: '99'}))
        self.rejected(lambda: p.validate_coverage(self.prod, 'corrected', self.axis, self.policy))

    def test_wrong_genotype_crosstab_rejected(self):
        self.edit_table(self.prod / 'corrected_resolution1_by_genotype.tsv', lambda x: x[0].update(WT='99'))
        self.rejected(lambda: p.validate_coverage(self.prod, 'corrected', self.axis, self.policy))

    def test_wrong_joint_library_coverage_rejected(self):
        self.edit_table(self.prod / 'corrected_resolution1_animal_library_condition_coverage.tsv',
                        lambda x: x[0].update(library_id='wrong'))
        self.rejected(lambda: p.validate_coverage(self.prod, 'corrected', self.axis, self.policy))

    def test_wrong_old_new_contingency_rejected(self):
        self.edit_table(self.prod / 'corrected_resolution0_6_vs_1_contingency.tsv', lambda x: x[0].update({'0': '99'}))
        self.rejected(lambda: p.validate_coverage(self.prod, 'corrected', self.axis, self.policy))

    def test_missing_second_graph_receipt_rejected(self):
        (self.prod / 'uncorrected_graph_complete.json').unlink()
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_missing_second_marker_branch_rejected(self):
        self.edit_json('marker_review_resolution1/complete.json', lambda x: x.update(branches=['corrected']))
        self.rejected(lambda: p.validate_receipts(self.prod, self.policy))

    def test_real_adapter_vectors_and_NA_semantics(self):
        staging = self.root / 'synthetic_adapters'; staging.mkdir()
        data = {b: self.check_markers(b) for b in self.policy['graphs']}
        coverage = {b: p.validate_coverage(self.prod, b, self.axis, self.policy) for b in self.policy['graphs']}
        p.make_adapters(staging, self.axis, data, self.panels, coverage, self.policy)
        self.assertEqual((staging / 'corrected_labels.u16le').stat().st_size, 4 * 2)
        adapter = load(staging / 'corrected_activity_adapter.json')
        self.assertEqual(sum(c['n'] for c in adapter['clusters']), 4)
        self.assertTrue(all(r[4:] == [None, None, None] for r in adapter['records'] if r[2] == self.genes[-1]))
        self.assertFalse(adapter['final_qc_available']); self.assertFalse(adapter['final_labels_available'])

    def test_review_needed_does_not_publish_validated_manifest(self):
        out = self.root / 'synthetic_review'; out.mkdir()
        p.review_needed(out, self.prod, self.policy, 'synthetic_package_job', {'synthetic_only': True}, 'synthetic timeout')
        result = load(out / 'stage_result.json')
        self.assertFalse(result['package_published'])
        self.assertFalse((out / 'validated_package_manifest.json').exists())
        self.assertTrue((out / 'review_partials/corrected_graph_complete.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
