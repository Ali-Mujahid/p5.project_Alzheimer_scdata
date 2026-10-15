# Additive ATAC Leiden resolution1 candidate

Existing resolution0.6 outputs and the accepted job7466270 atlas remain untouched. This source computes resolution1.0 on **both saved corrected and uncorrected neighbor graphs** with the original Leiden backend/settings made explicit: Scanpy1.11.5, leidenalg0.10.2, igraph0.11.9, RBConfigurationVertexPartition, weighted directed graph, n_iterations=-1 and seed1729. Only resolution changes. Cluster numbers are branch/resolution-specific and are not automatically comparable cell types.

No TF-IDF, LSI, Harmony, neighbors or UMAP is recomputed. The peak atlas is opened read-only by h5py and only `/obs` plus the two connectivity groups are read; raw peak X is never accessed. The saved graph identities are float32 CSR,456472x456472, corrected25131608 and uncorrected25050706 nonzeros. Each graph is loaded, clustered, checked for unchanged CSR content, then released before the other graph and activity stage. The source atlas byte/inode/mtime is checked before/after and every30seconds. No H5 atlas is written.

A real new marker stage follows graph release: one10000-row pass over accepted raw gene-body activity, full-gene count denominators and107 marker genes, aggregated into each **new** corrected/uncorrected cluster x animal membership. It reuses an exact copied `marker_review.py` aggregate helper and marker_panels.json from accepted source1602256721588ea9839ec42b5e0c5ca77793c278ee46d5ef3cf1683d0a59d115. No old0.6 marker summaries are relabeled as1.0. Accessibility is not RNA expression. Unmapped marker genes are explicitly NA, not false absence. Equal-animal means include observed animals with explicit coverage; no phantom animal or cell is inserted.

The existing456472 initial QC nuclei are retained here. This is an additive diagnostic sensitivity analysis, independent of the running full RNA/ATAC QC retention stage. Resolution1 annotation, final doublets/retention, rare-type peak refinement and final biological inference remain pending. Original0.6 graphs/labels/markers are protected comparison objects.

## Runtime and allocation

Use only the preserved absolute rna_py312 Python. No R module/load/install is needed. Clear PYTHONPATH/PYTHONHOME, disable user Python packages/bytecode, cap effective numerical thread variables at2. Actual versions were observed by root at2026-10-14T21:32UTC and are pinned in policy.json. The source-level Scanpy1.11.5 API audit confirms its prior `directed=None` resolves to `True` for leidenalg, defaults weights=True/n_iterations=-1 and RBConfigurationVertexPartition. No silent switch to the igraph Leiden implementation is permitted.

The allocation runs a tiny **actual installed-runtime** synthetic12-cell H5 graph reader/Leiden/reproducibility fixture and the copied sparse marker helper before any study graphs. The fixture requires two expected disconnected partitions, deterministic seed repeats, unchanged CSR and restricted H5 access; it is not study science or a benchmark.

Request2CPU/16GiB/2hours on one node, no requeue. This is a resource estimate, not a completion ETA. Sparse CSR itself is about200MB per graph; igraph conversion can require several GB of edge objects. The two graphs and their igraph representations are processed sequentially. Activity chunks and selected-marker summaries follow after graph release. A measured failure must preserve partials and be reviewed before a new additive attempt; no retry loop exists.

## Safety/evidence contract

The wrapper requires actual RUNNING owner10796/account molecular_neurosciences, exact CPU/memory and finite time, approved source/input pins, current fixed matched605GB/53000-inode headroom including in-doubt, and one unchanged shared500GB/40000-inode RNA+ATAC output allowance. It imports the read-only pinned Full_QC_v4 guard; every30s its own-process child/descendant open-unlinked FD monitoring charges the shared budget. A stricter1GB/4000-inode own-stage bound also charges output/temp/logs/final receipts and open unlinked files. These are sampled operational bounds.

R/SSH/job submission, cancellation, dependency modification, installation, cleanup and source/atlas mutation are absent. A stage lock and atomic one-use execution intent prevent duplicate stage execution. Child runs in its own process group and cwd/TMPDIR; exceptions/signals/storage failure trigger scoped TERM/wait/KILL/reap. All failed attempts, logs and generated partials stay preserved. Accept only matching source/input proofs, successful wrapper/science/storage receipts and unique whole+batch terminal0. Written intermediate labels are provisional while the allocation remains running.

## Outputs

- `cell_resolution0_6_and_1_assignments.tsv.gz`: exact canonical cell-ID join, original two0.6 columns, both new1.0 columns and animal/library/condition/genotype/sex.
- Corrected and uncorrected1.0 cluster summaries, animal/library/condition/genotype/sex counts, joint coverage, QC quantiles, per-animal QC and0.6x1.0 contingencies.
- `marker_review_resolution1/{corrected,uncorrected}/`: actual new markers_by_cluster_animal.tsv, equal_animal_markers.tsv, symbol_audit.tsv and completion/provenance. The compatibility column `initial_cluster` in these marker tables explicitly refers to that branch's1.0 IDs.
- Tiny runtime fixture, actual runtime/API/source digest, graph-preservation digests, graph/science/execution/storage completion or failed receipts, quota and storage logs.

Root must independently verify current remote input identity/source/runtime pins, deploy the new immutable source and submit once under its actual authorization. This directory is currently a local candidate only; no remote execution or study result is claimed by its preparation.

Primary API source inspected: https://raw.githubusercontent.com/scverse/scanpy/1.11.5/src/scanpy/tools/_leiden.py
