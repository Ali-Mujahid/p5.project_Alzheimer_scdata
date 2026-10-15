# Source-backed atlas QC status

The added `#qc-progress` section is independent of the initial ATAC view filters.
It loads `atlas_preview/qc_status.json` with `cache: no-store`. Every remote state
has its own observation time, and accepted candidate/technical reports have
their acceptance time. No remote polling or study matrix read occurs in this
adapter.

The builder binds source receipt/report SHA-256 fingerprints and the three
frontend assets into `qc_status_import_provenance.actual.json`. Source files and
scientific renderers are preserved; the UI has no new plot export buttons.
Existing linked QC figures are PDF, with TSV/JSON table/evidence links.

To bind a newly submitted reconciled gather after its actual proof exists:

```
python3 -B work/atlas_QC_status_20261015/build_status.py --gather-submission work/overnight_LiSC_20261015/QC_operational_reconciliation.submit.actual.json --additional-strict-route-review work/ATAC_QC_operational_recovery_20261015/two_new_terminal_QC_routes_200_201_review.actual.json
node work/atlas_QC_status_20261015/check_status.cjs
python3 -B work/atlas_QC_status_20261015/check_bindings.py
```

The gather gate requires the reviewed frozen manifest and exact whole-array
dependency on both 7471575 and 7472294. The latest timestamped combined local
observer proof is selected automatically. A specific proof may be supplied
using `--observation`, with the same two-array observer schema. An expanded
failure roster requires a new reviewed adapter; it is not silently substituted.
Every claimed accepted ATAC terminal index must also be in an actual strict
route review of its source, inputs, failure ancestry, successful whole/batch,
fixtures, nonce and storage receipts. `--strict-route-review` can supply a later
accepted proof. `--additional-strict-route-review` joins a separate actual review
of newly completed routes with the old proof, without modifying either. Repeated
proof paths, overlapping indices and reused physical jobs are rejected; accepted
counts are distinct logical indices, never a sum of repeated reports.
Future paired accounting completions without that proof stop
the builder instead of silently becoming accepted outputs. The public compact
summary and provenance bind the six-route review; no full large report is copied.

`protected_baseline.actual.json` records 12 original scientific JS/CSS/coordinate
assets. `status_checks.actual.json` binds source bytes, validates public report
links and numerical scope, and verifies these protected bytes are unchanged.
`render_checks.actual.json` checks the real renderer with a lightweight text DOM,
including missing-data and unsupported-schema error states. Root performs the
actual browser review; this subtask does not operate the browser.
