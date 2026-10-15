"""Synthetic negative boundaries for joining separately accepted local routes."""
from datetime import datetime, timezone
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
ATLAS = ROOT / 'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
BASE = ROOT / 'work/ATAC_QC_operational_recovery_20261015/six_terminal_QC_routes_review.actual.json'
ADDED = ROOT / 'work/ATAC_QC_operational_recovery_20261015/two_new_terminal_QC_routes_200_201_review.actual.json'
OBS = ROOT / 'work/ATAC_QC_operational_recovery_20261015/active_recovery_observation_20261015T095638Z.actual.json'
proof = json.loads(ADDED.read_text())
old = json.loads(BASE.read_text())
protected = [ATLAS / 'qc_status.json', ATLAS / 'qc_status_import_provenance.actual.json', BASE, ADDED]
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
before = hashes()
checks = {}
with tempfile.TemporaryDirectory(prefix='route_union_', dir=WORK) as temp:
    folder = Path(temp)
    invalid = copy.deepcopy(proof)
    invalid['all_selected_strict_checks_passed'] = False
    bad = folder / 'failed_review.synthetic.json'
    bad.write_text(json.dumps(invalid))
    overlap = folder / 'overlap_review.synthetic.json'
    overlap.write_text(json.dumps(old))
    reuse = copy.deepcopy(proof)
    reuse['route_reviews']['200']['physical_job_id'] = old['route_reviews']['192']['physical_job_id']
    reused = folder / 'reused_physical.synthetic.json'
    reused.write_text(json.dumps(reuse))
    cases = [
        ('stale six-route proof cannot accept two new completions', [], 'Terminal routes without strict acceptance proof'),
        ('missing added proof', [str(folder / 'missing.synthetic.json')], 'FileNotFoundError'),
        ('unsuccessful review refused', [str(bad)], 'Strict review must be read-only with all selected checks passed'),
        ('overlapping distinct reports refused', [str(overlap)], 'Overlapping route reviews need an explicit conflict review'),
        ('duplicate same proof refused', [str(BASE)], 'Duplicate strict review paths'),
        ('one physical job cannot certify two libraries', [str(reused)], 'A physical job cannot certify two logical libraries'),
    ]
    for name, additional, expected in cases:
        command = ['python3', '-B', str(WORK / 'build_status.py'), '--observation', str(OBS)]
        for p in additional:
            command += ['--additional-strict-route-review', p]
        result = subprocess.run(command, capture_output=True, text=True)
        checks[name + ': fail closed'] = result.returncode != 0
        checks[name + ': expected boundary reason'] = expected in result.stderr
        checks[name + ': actual proofs and last accepted public outputs preserved'] = hashes() == before
assert all(checks.values()), {k: v for k, v in checks.items() if not v}
report = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed_strict_route_union_negative_boundaries',
          'checks': checks, 'n_checks': len(checks), 'synthetic_only': True,
          'remote_queries': False, 'actual_proofs_modified': False}
(WORK / 'route_union_checks.actual.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'n_checks': len(checks), 'all_passed': True}))
