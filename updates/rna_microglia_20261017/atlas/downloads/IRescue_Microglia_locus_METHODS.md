# IRescue PRIMARY: Microglia TE-copy RNA matrices — 28 October 2026

IRescue is the user-selected primary RNA TE method. Stellarscope is preserved as a separately labeled comparison. No counts are combined across methods.

## Completed scope and input

All 22,251 selected Microglia cells, 44,502 corrected unmerged RT captures, 192 source libraries and 20 mice (five groups, four mice per group; two females and two males) were included. The inputs were the original selected RNA alignment records saved as `tagged.bam` during Microglia preparation. The folder name contains Stellarscope, but these are **not Stellarscope-reassigned alignments or count matrices**. The same exact source BAMs underlie the separate Stellarscope comparison. No FASTQ re-alignment or all-cell-type recount was performed.

New derived BAMs preserve every selected alignment, both mates, secondary/supplementary flags and UB UMI tags. CB tags are bijectively renamed from `SRR:barcode20` to `SRR.barcode20` because the stock IRescue AWK tag reader truncates a colon-bearing value. Source/library and corrected unmerged RT identity remain distinct. Original BAMs and Stellarscope count products are unchanged. The earlier IRescue subfamily adapter already used safe `EasySci_library.barcode` IDs; this compatibility adapter concerns the newly reused tagged BAMs.

## Reference and counting

All 3,651,522 existing mm10 RepeatMasker intervals were used, with unique coordinate/strand/subfamily IDs, **before** extracting ATAC-selected sets. No alternative TE loci were removed to favor selected peaks. BED0 coordinates are unchanged, and fragmented intervals were not silently joined into intact insertions. Each matrix retains exactly the original target-specific peak-bound TE row set, its annotations, and the same eight mouse columns, including all zero rows.

The pinned IRescue v1.2.0 source is commit `26f36fb391bb031a156ae8f0a77f31c125bfbe15`. `count.py` and `em.py` are unmodified. The previously checked shell/producer overlay checks command return codes and producer failures. The run uses `--locus-level fragment`, CB and UB tags, unstranded overlap, `--dump-ec`, `--keeptmp`, maximum 1,000 EM iterations, and likelihood convergence tolerance 0.0001. No integer conversion or low-support exclusion was requested.

## Count meaning and QC

These are **fractional expected UMI-cluster allocations**, including integer-looking values. They are not direct integer observations of physical transcripts. The stock per-capture export rounds to three decimals and omits allocations below 0.001. Across all mice, pre-export algorithm cluster mass was 4,962,885, exported expected mass was 4,962,706.130000, and the signed difference was -178.870000 (0.003604% loss). EC parsing preserved trailing empty fields and reconciled export mass per capture with a source-derived rounding bound. Do not round these counts for integer-only software.

All completed mice passed selection/axis/source-identity and numerical checks; all capture EM fits either converged or required no EM. The generated locus fixture preserved two distinct loci of one subfamily and recovered seven expected UMI clusters, including fractional allocations. This verifies a known algorithmic example, not physical transcript truth for the experimental data. Locus-level deduplication can retain UMI collisions collapsed at subfamily level, so sums need not equal the previous independently fitted 1,075-subfamily IRescue matrix.

Genome-wide, 1,073,766 of 3,651,522 intervals have positive expected counts after export; 801,278 have total expected count at least one across 20 mice. Positive fractional allocation is not independent evidence that every candidate copy was transcribed.

## Four raw matrices

| Target versus WT_3mo | Fixed TE rows | Control mice | Target mice |
|---|---:|---:|---:|
| WT_6mo | 9,361 | 4 | 4 |
| WT_21mo | 9,725 | 4 | 4 |
| 5xFAD_3mo | 7,240 | 4 | 4 |
| APOE4_TREM2_3mo | 6,438 | 4 | 4 |

Columns: TE_locus, chr, start, end, strand, TE_subfamily, TE_family, TE_class, followed by eight mouse-level raw RNA count columns. A target-only ATAC peak means a peak was called in that target and not control; it does not impose zero RNA expression in control. Within each comparison, control and target RNA counts refer to the **same TE copies**.

## Plots and method comparison

Boxplots use log2(1 + set RNA counts / gene-derived TMM effective library size × 1,000,000), with the same independent gene exposure for both methods. No locus-wise scaling is used for these aggregate boxplots. Every point is a mouse; no cells or TE loci are treated as biological replicates. Raw matrices are unnormalized. Set sizes differ across panels; compare control and target within a panel, rather than interpreting different set totals as between-target effects.

The heatmap PDF contains an overview of every original row plus a labeled 100-most-variable-locus view for each target. Heatmap values are within-locus z-scores of log(1 + gene-normalized counts); constant/zero rows are retained as zero display values. These are expression-variation heatmaps, not significance-selected differential genes/TEs. All rows remain in the downloadable matrices.

The methods scatterplots use the fixed 41,965-locus union of target-only and control-only sets. Descriptive target/control fold changes use gene-normalized group means and a one-CPM pseudocount; plotted loci have total count ≥5 in at least one method. This display filter does not remove rows from any raw matrix. There are no formal differential-expression P-values in this release.

IRescue uses per-capture expected allocation; the completed Stellarscope analysis uses mouse-level pseudobulk fitting and best_exclude hard assignments. They also differ in overlap requirements, UMI handling and treatment of non-TE alternatives. Both reuse alignments capped at 100 genomic placements. Differences in counts, zeros or disease direction do not establish superiority of either method. This is a matched-input sensitivity comparison, not a ground-truth accuracy benchmark. Nuclear, unstranded RNA overlap can include intronic/read-through signal; it does not certify autonomous TE transcription.

Official documentation: https://github.com/bodegalab/irescue . Method publication: https://pmc.ncbi.nlm.nih.gov/articles/PMC11514465/ .
