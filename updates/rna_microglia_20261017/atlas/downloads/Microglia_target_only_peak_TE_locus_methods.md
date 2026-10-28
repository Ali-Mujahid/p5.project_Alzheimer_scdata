# Normalization audit: Microglia RNA at ATAC peak-bound TE loci

## Why the 5xFAD direction changed

The earlier plot summed assigned RNA signal over a fixed locus set, divided by each mouse's total assigned TE signal, and normalized for the number of loci. The subsequent plot first applied log1p and a separate z-score to every locus, then averaged those scores. This changed the quantity being summarized as well as the display scale. A positive linear z-score applied to the original set total cannot reverse its ordering; this invariant was checked directly for every mouse in all eight sets.

The current main figure scales the **set total after normalization**. The previous equal-locus average remains in the comparison figure, explicitly labeled. Its stronger weighting of sparse features makes it sensitive to detection and sampling depth. Per-locus scaling follows the usual feature-centering/scaling concept, but the average of these scores is a different statistic from total expression ([Seurat ScaleData](https://satijalab.org/seurat/reference/scaledata)).

## Verified 5xFAD result

For the 7,240 TE copies overlapping 5xFAD-only MAnorm peaks:

- 4,547 loci have zero assigned RNA counts across all eight mice.
- 1,788 loci have only 1–4 counts across all eight mice.
- Mean TE-CPM is higher in 5xFAD at 1,216 loci and lower at 1,477 loci; these are descriptive directions, without a significance threshold.
- The increasing loci contribute +4,181.67 summed TE-CPM and decreasing loci contribute −3,284.15, giving a positive net change of +897.52 summed TE-CPM.
- Four WT_3mo mice have a median 1,106.5 selected Microglia and 219,509.5 assigned TE UMIs; the four 5xFAD mice have medians of 479.5 cells and 86,720 assigned TE UMIs. Total-TE normalization adjusts the depth denominator, but log transforms and averaging sparse locus scores remain sensitive to detection depth.

A seeded sensitivity analysis samples without replacement to 80,687 assigned TE UMIs per mouse, retaining the category of UMIs outside the selected TE set. Across 100 technical resamples, the median difference in the equal-locus score is 0.0093 (technical 2.5–97.5 percentiles 0.0028 to 0.0153), compared with −0.1005 before matching. The median total-signal ratio remains about 1.069. This shows strong technical sensitivity of the negative equal-locus display. Technical resamples do not add biological replicates, and these percentiles are not biological confidence intervals or a significance test.

## Alternative normalization results

Entries are target/WT_3mo ratios of the four-mouse medians, measured before z-scoring the set totals. A ratio of 1 means equal medians. All target-only peak-bound loci are retained.

| Target | Total-TE depth | TE TMM | Gene RNA depth |
|---|---:|---:|---:|
| WT_6mo | 1.015 | 0.999 | 1.042 |
| WT_21mo | 0.964 | 0.968 | 1.024 |
| 5xFAD_3mo | 1.066 | 1.044 | 1.015 |
| APOE4_TREM2_3mo | 0.973 | 0.961 | 0.999 |

The 5xFAD set-wide median is slightly higher with all three denominators. No tested normalization supports a uniform increase across all four target groups. Gene-depth normalization yields ratios close to one. These are descriptive ratios and do not establish statistical significance.

## Definitions and appropriate use

1. **Total-TE normalized set signal:** sum of assigned RNA UMIs in the set / all assigned TE UMIs in that mouse × 1e6 × 1000 / number of loci. This measures the set's relative share of the assigned TE transcript signal. The main figure uses z = (signal − eight-mouse mean) / eight-mouse sample SD. Every original mouse ordering and the sign of the median group difference are preserved.
2. **TMM TE normalized set signal:** replace the total-TE denominator with the TMM effective library size estimated from all 1,075 TE subfamilies across all 20 mice, using installed edgeR 4.2.2. This addresses relative RNA composition under TMM assumptions; it cannot measure a global absolute TE shift. The same fixed TE loci are summed. See the [edgeR normalization guide](https://bioconductor.org/packages/release/bioc/vignettes/edgeR/inst/doc/edgeRUsersGuide.pdf).
3. **Gene RNA depth normalized set signal:** replace the denominator with saved raw gene RNA UMI depth from the exact same 22,251 selected Microglia cells and 20 mice. All selected cell counts and animal IDs match the Stellarscope metadata. This measures TE signal relative to gene RNA depth. TE and gene counts come from different counting models; this is a sensitivity normalization, not an absolute TE transcript fraction.
4. **Previous equal-locus scaling:** log1p of each locus's TE-CPM, followed by a z-score of each locus across eight mice and an average of all locus z-scores per mouse. Constant loci receive zero. This emphasizes relative locus patterns; it can give a different answer to a summed set signal and is particularly depth-sensitive here.

All analyses use four biological mice per condition, balanced two female and two male; circles are females and triangles males. No TE loci or mouse samples were selected to obtain a desired RNA direction. All eight target/control-only peak-bound sets passed original count-sum conservation and the prior locus-score reproduction checks.

## What target-only accessibility predicts

The sets were selected using ATAC peak calls, not RNA expression. A target-only called peak does not require an RNA increase at that TE copy, and a TE-overlapping regulatory interval may affect a nearby gene without producing autonomous TE transcription. RNA and ATAC are from corresponding animals but different cells. The expectation of higher RNA expression is a hypothesis; it cannot be imposed through normalization or a direction-based locus filter.

For the original request to compare RNA signal over a fixed TE set, use the summed normalized expression and scale that same summary across mice. Retain the normalization sensitivity comparison. For formal differential-expression inference, analyze count data with mouse replicates and relevant covariates; the display z-scores are not inputs to a count model. Cross-model assignment uncertainty and the small magnitude of the aggregate changes remain relevant.

## Files and provenance

- `Microglia_target_only_peak_TE_locus_RNA_boxplots.pdf`: corrected scaled set totals, target-only and control-only sets.
- `Microglia_TE_RNA_normalization_comparison.pdf`: all four display/normalization methods for target-only loci, control-only loci, and 5xFAD contribution diagnostics.
- `normalization_mouse_values.tsv` and `normalization_group_summary.tsv`: all values and group medians.
- `locus_reversal_diagnostics.tsv`, `locus_count_bucket_diagnostics.tsv`, and `5xFAD_target_only_locus_diagnostics.tsv`: direct tracing of the reversal.
- `TE_TMM_factors.tsv`: TMM factors and library sizes.
- `5xFAD_equal_depth_technical_sensitivity.tsv` and `.json`: reproducible technical depth sensitivity.
- `audit_receipt.json`: source hashes, exact mouse/cell joins, and conservation checks.

Source matrices, peak sets, feature-axis joins and all preceding plot versions remain retained in the parent work directory. The calculations reuse saved small matrices; no BAM recount was performed.
