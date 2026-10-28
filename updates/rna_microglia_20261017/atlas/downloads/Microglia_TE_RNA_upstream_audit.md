# Microglia RNA TE-copy counting audit — 28 October 2026

The full-genome audit completed on LiSC (job 7752266). The exported count matrices exactly reproduce the original Stellarscope assignments. No barcode, locus-index, UMI-aggregation or selected-matrix export discrepancy was found in the checks below. This does not establish that the alignment/annotation/model captures every biological TE transcript.

## Counts independent of ATAC peak selection

| Scope | Annotated intervals | RNA-detected intervals | Zero across all 20 mice | Assigned RNA UMIs |
|---|---:|---:|---:|---:|
| All annotated TE loci | 3,651,522 | 804,504 | 2,847,018 (77.97%) | 4,351,598 |
| ATAC-selected union | 41,965 | 22,087 | 19,878 (47.37%) | 309,441 |
| Outside ATAC-selected union | 3,609,557 | 782,417 | 2,827,140 (78.32%) | 4,042,157 |

All 3,651,522 annotation intervals were tested, including zero rows. The downloadable `detected_TE_loci_all20_raw_counts.tsv.gz` contains every locus with at least one assigned count in any mouse, without any ATAC selection; all-zero reference rows are omitted explicitly to keep the file compact. The complete zero-inclusive reference remains in the original matrices and `te_loci.tsv`. Each column is a mouse and each value is an unnormalized, integer, locus-assigned RNA UMI count.

Across the full 1,075-subfamily table, 1,057 subfamilies have at least one count and 18 have none. Across 22,251 selected Microglia, the mean is 195.6 assigned TE UMIs per cell. These counts are distributed very unevenly among millions of genomic annotation fragments. More detected genomic copies should not be inferred from a subfamily-level total.

Of the 2,847,018 zero-count loci, 2,763,982 never appear as an eligible TE candidate in the saved input score matrices of any mouse; 83,036 have candidate support but no final count after deduplication/assignment. The first category includes absent sequencing support, alignment loss, insufficient overlap and a neighboring overlapping annotation winning the overlap rule. It does not prove biological silence.

## Exact upstream-to-export checks

1. All 20 selected BAM headers use mm10 (chr1 length 195,471,971), contain the 192 original STAR provenance records, and retain a STAR multimapping limit of 100. Header checking does not recover reads rejected during alignment.
2. All 20 selection reports have observed = expected corrected unmerged RT captures, totaling 44,502 captures for 22,251 selected cells. CB includes source library/run; UB is the original eight-base UMI. The two RT capture layers remain separate during deduplication. Both mates and secondary alignments are retained by the selection code.
3. All 3,651,522 TE feature positions in every saved checkpoint exactly match the full RepeatMasker locus reference. BED start+1 to GTF start is the intended coordinate conversion. The `__no_feature` background row is excluded from TE totals rather than shifted into the first TE locus.
4. Independently reconstructing unique (capture barcode, UMI, TE locus) triples from the original `best_exclude` assignment matrix exactly reproduces every locus count in all 20 original matrices, including the background row. This also checks the vectorized group-by patch on real data, rather than relying only on generated tests.
5. All 1,075 × 20 subfamily totals are identical to the existing combined counts. All 41,965 × 20 previously exported locus values are identical to the newly reconstructed original locus sums. Source matrix/checkpoint inode, size and modification time are unchanged across reads.
6. Full raw counts are nonnegative integers and sum to 4,351,598 TE UMIs. No CPM, z-score, filtering or ATAC coverage was used to create these counts.

## Method limits identified — do not interpret zeros as proven absence

- **Alignment sensitivity:** the source STAR runs allow at most 100 alignment locations; the Stellarscope tutorial uses 500. Reads exceeding the original limit are unavailable to downstream Stellarscope, and repeated analysis of the same BAM cannot recover them. The size of this loss has not been measured with a matched FASTQ re-alignment. It may especially affect repetitive/young copies; the actual age-specific effect has not been established.
- **Overlap rule:** the actual run uses the package's default threshold: the highest-overlap annotated locus must overlap strictly more than 20% of aligned fragment bases. It is not an any-overlap read counter. Very short RepeatMasker fragments may fail this criterion even when a read overlaps a few bases. Each RepeatMasker interval is an annotation fragment, not necessarily an intact TE insertion or autonomous transcript.
- **Ambiguous assignments:** `best_exclude` discards tied best posterior assignments: 27,076 of 4,388,645 post-dedup model observations (0.62%). This explains some losses but is too small to explain the majority of zero loci. A read with a unique best assignment still contributes to only its selected locus, not every alternative genomic copy.
- **Convergence audit gap:** `max_iter=500` was set. The official code writes convergence/iteration status at DEBUG level; the saved INFO logs and final count checkpoint do not retain enough information to independently prove convergence for every model. Successful Slurm completion does not close this gap. A recorded checkpoint re-fit is needed before claiming all-model convergence.
- **Unstranded nuclear RNA:** overlap counts can include intronic/read-through transcription. They do not by themselves identify autonomous or sense TE transcription. RNA and ATAC were measured in different nuclei.

## Interpretation and next validation

The ATAC-selected rows are sparse, but sparsity is also widespread genome-wide. Compare selected and unselected loci using the same eight mice, which the accompanying PDF does separately for each contrast. The selected and unselected loci differ in length, genomic context and mappability; these descriptive comparisons are not a matched enrichment test.

Use the existing subfamily/family measurements for the main RNA inference and retain copy-level results with explicit detection/mappability limits. For stronger copy-specific conclusions, perform (i) a recorded convergence re-fit from saved checkpoints, (ii) a bounded matched alignment sensitivity test at 100 versus 500 locations from the same original selected reads, and (iii) overlap-threshold/annotation-fragment sensitivity on those same reads. Do not select a normalization, assignment policy or threshold because it produces a desired target-versus-control direction. No scientific count matrix was replaced during this audit.

Official method: https://github.com/nixonlab/stellarscope/blob/main/docs/protocol.md . Audited implementation: Stellarscope 1.5, source commit `0e0d594047212afe81e3754732119975a0d2aa6f`.

## Files

- `Microglia_TE_RNA_upstream_audit.pdf`: all-locus detection, per-mouse sparsity, TE classes/lengths, subfamily abundance and same-eight-mouse comparisons.
- `audit.json`: full numerical audit, 20-mouse source/selection/model statistics.
- `detection_summary.tsv`, `subfamily_detection.tsv`, `top_TE_loci.tsv`: numerical summaries and independent-of-ATAC examples.
- `detected_TE_loci_all20_raw_counts.tsv.gz`: raw RNA count matrix for every genome-wide detected TE locus, all 20 mice, no ATAC filter.

LiSC directory: `/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/te-RNA/TE_RNA_upstream_audit_20261028_v2/output/`.
