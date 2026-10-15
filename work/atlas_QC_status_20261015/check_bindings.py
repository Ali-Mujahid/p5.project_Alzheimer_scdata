"""Validate the public status against its receipts and preserved atlas assets."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
W = Path(__file__).resolve().parent
d = json.loads((A / 'qc_status.json').read_text())
p = json.loads((A / 'qc_status_import_provenance.actual.json').read_text())
checks = {}
for key, value in json.loads((W / 'protected_baseline.actual.json').read_text()).items():
    checks['protected bytes ' + key] = hashlib.sha256((ROOT / key).read_bytes()).hexdigest() == value
for source in p['sources'] + [p['builder'], p['adapter']] + p['frontend_assets']:
    q = ROOT / source['workspace_path']
    checks['source exact SHA ' + source['workspace_path']] = hashlib.sha256(q.read_bytes()).hexdigest() == source['sha256']
for stage in ['rna', 'sct_technical_profile']:
    for key, value in d[stage].items():
        if key.endswith(('_pdf', '_tsv', '_json')):
            checks['public report link ' + value] = (A / value).resolve().is_file()
checks['distinct library total preserved'] = d['rna']['total_libraries'] + d['atac']['total_libraries'] == 296
checks['unverified repairs not substituted as completions'] = d['atac']['new_recovery']['accepted_completed'] == 0
checks['normalization and final retention remain unavailable'] = not any(d[x] for x in ['full_QC_complete', 'final_retention_complete', 'normalization_ready'])
checks['RNA candidate count matches report'] = d['rna']['candidate_cells'] == 2190200
checks['SCT unresolved candidates match accepted report'] = d['sct_technical_profile']['unresolved_candidate_cells'] == 6995
checks['all claimed ATAC completions have strict accepted route proofs'] = len(d['atac']['strict_route_review']['accepted_indices']) == d['atac']['accepted_completed'] and d['atac']['strict_route_review']['source_inputs_fixtures_storage_and_nonce_joined']
route_sources = d['atac']['strict_route_review']['sources']
checks['distinct strict source proofs bind exact accepted union'] = (len({x['workspace_path'] for x in route_sources}) == len(route_sources) and
    len([i for x in route_sources for i in x['accepted_indices']]) == len(set(i for x in route_sources for i in x['accepted_indices'])) and
    set(d['atac']['strict_route_review']['accepted_indices']) <= set(i for x in route_sources for i in x['accepted_indices']) and
    all(hashlib.sha256((ROOT / x['workspace_path']).read_bytes()).hexdigest() == x['sha256'] for x in route_sources))
html = (A / 'index.html').read_text()
checks['one QC navigation and target'] = html.count('href="#qc-progress"') == 1 and html.count('id="qcProgressApp"') == 1
checks['independent local script and CSS'] = html.count('src="qc_status.js"') == 1 and html.count('href="qc_status.css"') == 1
checks['no new PNG plot controls'] = 'PNG' not in (A / 'qc_status.js').read_text()
assert all(checks.values()), [k for k, v in checks.items() if not v]
report = {'utc': datetime.now(timezone.utc).isoformat(),
          'status': 'passed_source_binding_links_numerical_scope_and_protected_asset_checks',
          'checks': checks, 'n_checks': len(checks), 'all_passed': True,
          'root_browser_review_pending': True}
(W / 'status_checks.actual.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'n_checks': len(checks), 'all_passed': True}))
