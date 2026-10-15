# Leiden resolution 1.0 — actual verified import

Producer **7470007** completed both real corrected and uncorrected 12-cluster partitions and fresh 107-gene marker summaries. Package **7470531** completed successfully with matching execution, completion, storage and source evidence. Its exact allocated manifest SHA is `07fb6736f0304ca87225dd8449a548a579072a4223092d2c2589ad58e288cc02`.

The local import now verifies all 47 downloaded package file hashes and bytes, accepted ordered cell-axis SHA `6792e79c2f13c82c110b3b03011eb654abf043c733614c8aadfa9e34dfea9ad1`, existing point-attribute SHA, both actual label vectors, 456,472 nuclei, 20 animals, branch-specific cluster/animal counts and all 107 marker rows per group. Mapped raw sums remain nonnegative integers; five unmapped mitochondrial genes remain NA.

The HTML registry offers four actual partitions: 0.6 corrected (11 clusters), 0.6 uncorrected (9), 1.0 corrected (12) and 1.0 uncorrected (12). The existing real Harmony and uncorrected UMAP coordinates are reused unchanged as independent display backgrounds. Resolution-0.6 uncorrected has real labels/composition but no own activity summaries, so its activity plots and ranking are unavailable rather than reusing corrected means.

New resolution-1 cluster candidates are unreviewed. No old biological display label or microglia cluster-6 shortcut carries into a new numeric partition. Editable label mappings, exports and storage are scoped to each dataset/resolution/graph. PDF-only figure exports carry selected source/resolution/graph and coordinate context.

Proof: `resolution1_import_provenance.actual.json`. Tests: `resolution_selector_tests.actual.json` and the core/PDF QA records. Browser visual validation is performed and recorded separately by the parent task. No final QC, retention, cell identity, RNA integration or TE result is adopted by this import. No raw matrix, graph, H5AD, remote source or scheduler job was read, modified or rerun.
