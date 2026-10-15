"""Import only the downloaded, accepted small resolution-specific web adapters.

No remote access, raw matrix, AnnData, neighbor graph, or producer execution.
"""
import base64
import collections
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / 'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
PKG = ROOT / 'outputs/p5_workflow/ATAC_initial_atlas_20261014/job-7470007/resolution1_package_job-7470531'
EXPECTED = '07fb6736f0304ca87225dd8449a548a579072a4223092d2c2589ad58e288cc02'
AXIS = '6792e79c2f13c82c110b3b03011eb654abf043c733614c8aadfa9e34dfea9ad1'
ATTRS = '1496e75782c426fdd026af00c4f3dc98312629492b8ba9e13928d0896892a897'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def js_object(p):
    s = p.read_text()
    return json.loads(s[s.index('=') + 1:].strip().rstrip(';'))


def main():
    manifest_path = PKG / 'validated_package_manifest.json'
    assert sha(manifest_path) == EXPECTED
    manifest = json.loads(manifest_path.read_text())
    review_path = PKG / 'terminal_package_review.actual.json'
    review = json.loads(review_path.read_text())
    assert review['HTML_adapter_import_authorized'] is True
    assert review['initial_diagnostics_accepted'] is True
    assert review['checks_passed'] == 10 and all(review['checks'].values())
    assert manifest['upstream_job_id'] == '7470007' and manifest['package_job_id'] == '7470531'
    assert manifest['ordered_cell_ids_sha256'] == AXIS
    assert manifest['initial_point_attribute_bytes_sha256'] == ATTRS
    verified = []
    for rel, ident in manifest['files'].items():
        p = PKG / 'validated_products' / rel
        assert not p.is_symlink() and p.is_file()
        assert p.stat().st_size == ident['bytes'] and sha(p) == ident['sha256'], rel
        verified.append({'path': str(p.relative_to(ROOT)), 'bytes': ident['bytes'], 'sha256': ident['sha256']})
    old = js_object(WEB / 'data_adapter.js')
    attrs = js_object(WEB / 'point_attributes.js')
    raw = base64.b64decode(attrs['base64'], validate=True)
    assert hashlib.sha256(raw).hexdigest() == ATTRS and len(raw) == 456472 * 3
    attr_animals = attrs['animals']
    extra = {}
    for branch in ('corrected', 'uncorrected'):
        d = json.loads((PKG / 'validated_products' / f'{branch}_activity_adapter.json').read_text())
        assert d['ordered_cell_ids_sha256'] == AXIS and d['initial_point_attributes_sha256'] == ATTRS
        assert d['partition_graph'] == branch and d['resolution'] == 1.0 and d['n_cells'] == 456472
        assert len(d['clusters']) == 12 and len(d['genes']) == 107 and len(d['animals']) == 20
        labels = (PKG / 'validated_products' / f'{branch}_labels.u16le').read_bytes()
        assert len(labels) == 456472 * 2
        dictionary = manifest['adapters'][branch]['label_dictionary']
        counts = collections.Counter()
        for i in range(456472):
            code = int.from_bytes(labels[i * 2:i * 2 + 2], 'little')
            assert code < len(dictionary)
            counts[dictionary[code], attr_animals[raw[i * 3 + 2]]] += 1
        observed = {}
        mapped = {g['symbol']: g['mapped'] for g in d['genes']}
        seen = set()
        for c, a, g, n, total, detected, normalized in d['records']:
            key = (c, a, g)
            assert key not in seen and n == counts[c, a] and n > 0
            seen.add(key)
            observed[c, a] = n
            if mapped[g]:
                import math
                assert isinstance(total, int) and total >= 0 and 0 <= detected <= 1
                assert math.isfinite(normalized) and normalized >= 0
            else:
                assert total is None and detected is None and normalized is None
        assert len(seen) == 12 * 20 * 107 and observed == dict(counts)
        assert {c['id']: c['n'] for c in d['clusters']} == {c: sum(n for (cc, _), n in counts.items() if cc == c) for c in dictionary}
        extra[branch] = {'coverage_records': [[c, a, n] for (c, a), n in sorted(counts.items())], 'label_dictionary': dictionary}

    # The initial uncorrected partition has its own real labels/coverage but no
    # independent gene-body marker summaries. Never reuse corrected means here.
    coverage_path = ROOT / 'outputs/p5_workflow/ATAC_initial_atlas_20261014/job-7466270/embedding/uncorrected_initial_cluster_by_animal_id.tsv'
    with coverage_path.open() as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        rows = [[r[0], a, int(n)] for r in reader for a, n in zip(header[1:], r[1:])]
    assert sum(r[2] for r in rows) == 456472 and len({r[0] for r in rows}) == 9
    # Exact agreement to the already exported original per-cell label axis.
    old_counts = collections.Counter((str(raw[i * 3 + 1]), attr_animals[raw[i * 3 + 2]]) for i in range(456472))
    assert {(c, a): n for c, a, n in rows} == dict(old_counts)
    rel = '../../ATAC_initial_atlas_20261014/job-7470007/resolution1_package_job-7470531/'
    config = {'schema_version': '1.0', 'manifest_sha256': EXPECTED, 'ordered_cell_ids_sha256': AXIS,
              'initial_point_attributes_sha256': ATTRS, 'package_path': rel,
              'resolution1': extra, 'initial_uncorrected_coverage': rows,
              'source_records': verified,
              'terminal_review_path': rel + 'terminal_package_review.actual.json'}
    (WEB / 'resolution_registry.js').write_text('/* Actual source-bound registry configuration; no synthetic cells. */\nwindow.ATLAS_RESOLUTION_REGISTRY_CONFIG=' + json.dumps(config, separators=(',', ':')) + ';\n')
    proof = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'accepted_small_adapters_imported',
             'package_manifest_sha256': EXPECTED, 'terminal_review_sha256': sha(review_path),
             'files_verified': len(verified), 'n_cells': 456472,
             'cluster_counts': {'0.6_corrected': 11, '0.6_uncorrected': 9, '1.0_corrected': 12, '1.0_uncorrected': 12},
             'resolution1_label_counts_match_actual_marker_animal_axis': True,
             'initial_uncorrected_coverage_matches_existing_labels': True,
             'initial_uncorrected_activity_available': False,
             'source_mapped_gene_nonnegative_integer_and_NA_checks': True,
             'coordinates_unchanged': True, 'raw_matrix_graph_or_h5_read': False,
             'final_QC_or_cell_types_adopted': False, 'source_records': verified,
             'registry_sha256': sha(WEB / 'resolution_registry.js')}
    (WEB / 'resolution1_import_provenance.actual.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({k: v for k, v in proof.items() if k != 'source_records'}, indent=2))


if __name__ == '__main__':
    main()
