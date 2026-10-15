"""Build a compact atlas status adapter from actual, local source-bound evidence.

This does not inspect study matrices, query Slurm or decide final retained cells.
An observation is a dated snapshot, never a promise of the current queue state.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / 'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
WF = ATLAS.parent


def read(path):
    p = ROOT / path
    return json.loads(p.read_text())


def bound(path):
    p = ROOT / path
    return {'workspace_path': str(path), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def verified_routes(paths):
    """Join distinct, actual strict route reviews without overwriting any proof."""
    canonical_paths = [str((ROOT / path).resolve()) for path in paths]
    assert len(set(canonical_paths)) == len(paths), 'Duplicate strict review paths are not a second acceptance'
    routes, sources = {}, []
    for path in paths:
        proof = read(path)
        assert proof['read_only'] and proof['all_selected_strict_checks_passed'], 'Strict review must be read-only with all selected checks passed'
        assert not any(proof[k] for k in ['full104_adoption', 'full296_adoption', 'normalization_ready'])
        selected = proof['selected_indices']
        assert len(set(selected)) == len(selected), 'Duplicate selected route index'
        assert set(map(int, proof['route_reviews'])) == set(selected)
        assert not set(routes).intersection(selected), 'Overlapping route reviews need an explicit conflict review'
        for index in selected:
            assert 192 <= index <= 295 and index not in (194, 195)
            route = proof['route_reviews'][str(index)]
            assert route['status'] == 'verified_provisional_QC_candidate_route'
            assert route['source_inputs_fixtures_storage_and_nonce_joined'] and route['original_failure_preserved']
            assert route['science']['assay'] == 'atac' and route['science']['task_index'] == index
            assert not route['science']['cell_types_used_for_filtering'] and not route['science']['raw_inputs_modified']
            accounting = route['actual_whole_batch']
            assert len(accounting) == 2 and {row['JobID'] for row in accounting} == {f'7471575_{index}', f'7471575_{index}.batch'}
            assert all(row['State'] == 'COMPLETED' and row['ExitCode'] == '0:0' for row in accounting)
            routes[index] = route
        sources.append({**bound(path), 'accepted_utc': proof['utc'], 'accepted_indices': sorted(selected)})
    assert len({route['physical_job_id'] for route in routes.values()}) == len(routes), 'A physical job cannot certify two logical libraries'
    return routes, sources


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--observation', help='Combined local observer proof; defaults to latest timestamped proof')
    ap.add_argument('--gather-submission')
    ap.add_argument('--strict-route-review', default='work/ATAC_QC_operational_recovery_20261015/six_terminal_QC_routes_review.actual.json',
                    help='Actual strict source/input/fixture/nonce/storage/accounting review required before accepting ATAC terminal routes')
    ap.add_argument('--additional-strict-route-review', action='append', default=[],
                    help='Separate actual strict review of newly completed routes; repeatable, disjoint indices required')
    args = ap.parse_args()
    if not args.observation:
        local = sorted((ROOT / 'work/ATAC_QC_operational_recovery_20261015').glob('active_recovery_observation_*.actual.json'))
        assert local, 'No actual combined local observations available'
        args.observation = str(local[-1].relative_to(ROOT))
    obs = read(args.observation)
    submission_path = 'work/overnight_LiSC_20261015/ATAC_QC_operational_recovery.submit.actual.json'
    sub = read(submission_path)
    rna_base = 'outputs/p5_workflow/full_workflow_20261014/QC_review_RNA_job-7471574/'
    sct_base = 'outputs/p5_workflow/full_workflow_20261014/SCT_technical_profile_job-7471609/'
    rna_cert_path = rna_base + 'summary/validated_QC_certificate.json'
    rna_review_path = rna_base + 'review/review_needed.json'
    rna_adoption_path = rna_base + 'terminal_adoption.actual.json'
    rna_complete_path = rna_base + 'terminal_evidence/complete.json'
    cert, review, adoption, rna_complete = map(read, [rna_cert_path, rna_review_path, rna_adoption_path, rna_complete_path])
    sct_review_path = sct_base + 'terminal_adoption.actual.json'
    sct_profile_path = sct_base + 'profile/complete.json'
    sct_complete_path = sct_base + 'complete.json'
    sct, profile, sct_complete = map(read, [sct_review_path, sct_profile_path, sct_complete_path])
    assert cert['logical_libraries_validated'] == 192 and cert['all_chosen_whole_and_batch_completed_0']
    assert adoption['status'] == 'root_adopted_independently_verified_scoped_outputs'
    assert not review['normalization_ready'] and not cert['normalization_ready']
    assert sct['all_checks_passed'] and sct['n_checks'] == 119 and not sct['final_normalization_complete']
    arrays = obs['arrays']
    prior, recovery = arrays['7471575'], arrays[str(sub['job_id'])]
    assert all(prior['source_checks'].values()) and all(recovery['source_checks'].values())
    assert recovery['source_manifest_sha256'] == sub['source_manifest_sha256']
    paired_indices = set(prior['unique_whole_batch_successes'])
    review_paths = [args.strict_route_review] + args.additional_strict_route_review
    route_reviews, route_review_sources = verified_routes(review_paths)
    reviewed_indices = set(route_reviews)
    assert paired_indices <= reviewed_indices, 'Terminal routes without strict acceptance proof cannot be accepted automatically'
    accepted = len(paired_indices)
    n_failed = prior['accounting_counts'].get('whole:FAILED', 0)
    running = prior['queue_counts'].get('RUNNING', 0)
    pending = prior['queue_counts'].get('PENDING', 0)
    assert accepted + n_failed + running + pending == 104
    assert n_failed == 2, 'An expanded failure roster requires a new reviewed adapter'
    with (ROOT / rna_base / 'summary/all_192_RNA_library_QC_summary.tsv').open() as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    basic = sum(int(r['n_basic']) for r in rows)
    assert len(rows) == 192
    summary = sct['summary']
    status = {
        'schema_version': 1,
        'built_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Actual dated QC progress and accepted candidate/technical reports; initial atlas views unchanged',
        'full_QC_complete': False,
        'final_retention_complete': False,
        'normalization_ready': False,
        'rna': {
            'job_id': 7471574, 'status': 'Candidate QC reports verified',
            'completed_libraries': cert['logical_libraries_validated'], 'total_libraries': 192,
            'completed_receipt_utc': rna_complete['utc'], 'accepted_utc': adoption['utc'],
            'candidate_cells': review['candidate_counts']['rna'], 'basic_supported_cells': basic,
            'doublet_unresolved_basic': review['doublet_unresolved_basic'],
            'libraries_without_automatic_mt_threshold': review['libraries_without_automatic_mt_threshold'],
            'source_manifest_sha256': cert['RNA_QC_source_manifest_sha256'],
            'report_pdf': '../QC_review_RNA_job-7471574/review/QC_animal_review.pdf',
            'library_tsv': '../QC_review_RNA_job-7471574/review/QC_by_library.tsv',
            'review_json': '../QC_review_RNA_job-7471574/review/review_needed.json',
            'certificate_json': '../QC_review_RNA_job-7471574/summary/validated_QC_certificate.json'
        },
        'atac': {
            'array_id': 7471575, 'observed_utc': obs['utc'], 'accepted_completed': accepted,
            'failed_attempts': n_failed, 'failed_tasks': [194, 195], 'running': running, 'pending': pending,
            'total_libraries': 104, 'source_manifest_sha256': prior['source_manifest_sha256'],
            'completion_rule': 'Unique successful whole and batch accounting plus matching execution, recovery and storage receipts',
            'strict_route_review': {
                'accepted_utc': max(route_review_sources, key=lambda item: datetime.fromisoformat(item['accepted_utc']))['accepted_utc'],
                'accepted_indices': sorted(paired_indices),
                'source_sha256': bound(args.strict_route_review)['sha256'],
                'sources': route_review_sources,
                'source_inputs_fixtures_storage_and_nonce_joined': True,
                'scope': 'Provisional QC candidate routes only; failed originals preserved; no full-104/full-296 or final-retention adoption'
            },
            'new_recovery': {
                'array_id': int(sub['job_id']), 'tasks': [194, 195], 'submitter': sub['submission_owner'],
                'submitted_utc': sub['utc'], 'observed_utc': obs['utc'],
                'queue_counts': recovery['queue_counts'], 'accounting_counts': recovery['accounting_counts'],
                'source_manifest_sha256': sub['source_manifest_sha256'],
                'started_receipts': recovery['receipt_counts'].get('started.json', 0),
                'accepted_completed': len(recovery['unique_whole_batch_successes']),
                'scope': 'Operational storage-check repair only; scientific QC code and inputs preserved'
            }
        },
        'sct_technical_profile': {
            'job_id': 7471609, 'status': 'Single-library technical profile verified',
            'completed_receipt_utc': sct_complete['utc'], 'accepted_utc': sct['utc'],
            'independent_checks_passed': sct['n_checks'], 'library_id': profile['selected_library_id'],
            'candidate_cells': summary['candidate_cells'], 'unresolved_candidate_cells': summary['unresolved_cells'],
            'fitted_gene_models': summary['fitted_genes'], 'unmodeled_genes': summary['missing_gene_models'],
            'candidate_HVG_count': summary['candidate_HVG_count'],
            'max_RSS_GiB': summary['scheduler_batch_MaxRSS_GiB'],
            'source_manifest_sha256': sct['source_manifest_SHA256'],
            'profile_json': '../SCT_technical_profile_job-7471609/profile/complete.json',
            'review_json': '../SCT_technical_profile_job-7471609/terminal_adoption.actual.json',
            'candidate_features_tsv': '../SCT_technical_profile_job-7471609/profile/profile_top3000_HVG_candidates.tsv',
            'limitations': 'One provisional candidate library, including unresolved flags. Missing models remain NA. No final study normalization, PCA, Harmony or clustering performed.'
        },
        'gather': {'status': 'New repair-aware full-296 gather being prepared; no completion accepted'},
        'interpretation': [
            'Candidate counts do not certify singlets or final retention.',
            'Both failed attempts remain FAILED in their original accounting. Separate recoveries cannot overwrite that history.',
            'Full 296-library reconciliation and documented retention decisions precede final normalization and embeddings.',
            'Every supported cell type and unknown candidate remains in scope; cell type is not a QC filter.'
        ]
    }
    paths = [args.observation] + review_paths + [submission_path, rna_cert_path, rna_review_path, rna_adoption_path,
             rna_complete_path, rna_base + 'summary/all_192_RNA_library_QC_summary.tsv',
             sct_review_path, sct_profile_path, sct_complete_path]
    if args.gather_submission:
        g = read(args.gather_submission)
        assert g['rc'] == 0 and g['job_id']
        assert g['dependency'] == 'afterany:7471575:7472294'
        assert g['source_manifest_sha256'] == 'd2d718a0921441309809f17129cafcdea8c6fa2df292e7213cb4668800df17a7'
        status['gather'] = {'job_id': int(g['job_id']), 'submitted_utc': g['utc'], 'submitter': g['submission_owner'],
                            'dependency': g['dependency'], 'source_manifest_sha256': g['source_manifest_sha256'],
                            'status': 'Repair-aware full-296 gather submitted; completion not yet accepted'}
        observed_gather = obs.get('operational_gather' + str(g['job_id']))
        if observed_gather:
            assert observed_gather['source_manifest_sha256'] == g['source_manifest_sha256']
            assert len(observed_gather['source_checks']) == 17 and all(observed_gather['source_checks'].values())
            queue = observed_gather['queue']
            assert queue['rc'] == 0
            queue_rows = [line.split('|') for line in queue['stdout'].strip().splitlines() if line]
            assert len(queue_rows) == 1 and queue_rows[0][0] == str(g['job_id'])
            state = queue_rows[0][1]
            status['gather']['observed_utc'] = obs['utc']
            status['gather']['scheduler_state'] = state
            if state == 'PENDING':
                assert 'afterany:7471575_*' in queue_rows[0][3] and 'afterany:7472294_*' in queue_rows[0][3]
                status['gather']['status'] = 'Queued on both whole-array prerequisites; completion not yet accepted'
            else:
                status['gather']['status'] = 'Observed scheduler state ' + state + '; completed outputs not yet accepted'
        paths.append(args.gather_submission)
    target = ATLAS / 'qc_status.json'
    target.write_text(json.dumps(status, indent=2) + '\n')
    provenance = {'utc': status['built_utc'], 'builder': bound(str(Path(__file__).relative_to(ROOT))),
                  'scope': status['scope'], 'sources': [bound(p) for p in paths],
                  'adapter': bound(str(target.relative_to(ROOT))),
                  'frontend_assets': [bound(str((ATLAS / name).relative_to(ROOT)))
                                      for name in ['index.html', 'qc_status.js', 'qc_status.css']],
                  'full_QC_complete': False, 'normalization_ready': False,
                  'no_study_matrix_or_BAM_scan': True, 'no_remote_query': True}
    (ATLAS / 'qc_status_import_provenance.actual.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'status': 'source_bound_QC_status_adapter_built', 'atac_observed_utc': obs['utc'],
                      'atac_completed': accepted, 'atac_running': running, 'atac_pending': pending,
                      'recovery_job_id': sub['job_id'], 'full_QC_complete': False}))


if __name__ == '__main__':
    main()
