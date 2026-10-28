# Microglia RNA signal at target-only ATAC peak-bound TE loci

## Inputs and sets

The four target-only peak-bound TE sets are the MAnorm native, unfiltered `unique_target` peak overlaps with the mm10 RepeatMasker TE BED. They contain 9,361 WT_6mo, 9,725 WT_21mo, 7,240 5xFAD_3mo, and 6,438 APOE4_TREM2_3mo distinct TE loci. For each pairwise comparison, a separate WT_3mo-only peak-bound TE set was constructed from the native `unique_control.bed` and the same TE annotation; these contain 8,188, 8,767, 10,136, and 10,615 loci, respectively. `unique` describes the called ATAC peak set, not exclusive RNA detection or exclusive TE-copy occupancy. Some TE copies overlap different peaks from both peak sets.

RNA input is the previously validated Stellarscope 1.5, Microglia-selected, per-animal TE-locus UMI matrix (20 mice, 22,251 selected cells). The mm10 feature axis is pinned by SHA256 `91c4d17962d10deab904f6fbd440f99d1d8c6d6a4f333db9f854ee9fcc0214ab`. All eight ATAC TE sets matched the Stellarscope feature axis exactly by chromosome, start, end, and strand; zero loci were missing and no locus matched more than one feature. ATAC BED TE names often differ from the more specific Stellarscope feature names, so no name-only join was used. See `results/feature_join_audit.json`.

## Measurement

For each mouse and locus set, RNA signal is the sum of Stellarscope-assigned TE UMIs over the matched loci. The plotted quantity is `set UMIs / all assigned TE UMIs in that mouse × 1,000,000 × 1,000 / number of matched loci`. Each panel compares exactly the same fixed TE locus set between four WT_3mo mice and four target mice, balanced two females and two males per condition. Boxplots show mouse-level values and every mouse point. The top row uses target-only ATAC peak-bound TE loci; the lower row uses the pairwise WT_3mo-only peak-bound TE loci.

This is a descriptive analysis. ATAC-only peaks can have RNA signal in either group. The assigned UMI values depend on the Stellarscope multimapping model and do not prove autonomous transcription from a TE copy. Equal total-TE-UMI normalization measures the share of model-assigned TE signal per 1,000 loci; it does not replace a formal count model with RNA depth and cell-composition offsets. No p-values or differential-expression calls are inferred from these boxplots.

## Results

The target-only-set median target/WT_3mo ratios are 1.015 (WT_6mo), 0.964 (WT_21mo), 1.066 (5xFAD_3mo), and 0.973 (APOE4_TREM2_3mo). Thus the group medians are similar at this aggregate scale; the 5xFAD panel shows the largest positive descriptive shift, about 6.6%. Individual loci can differ despite similar set-wide totals.

## Files

- `Microglia_target_only_peak_TE_locus_RNA_boxplots.pdf` and `.png`: eight panels.
- `Microglia_target_only_peak_TE_locus_mouse_values.tsv`: 64 mouse-by-set values, including raw and normalized sums.
- `Microglia_target_only_peak_TE_locus_summary.tsv`: descriptive group medians and ratios.
- The full per-locus selected UMI table is retained locally at `/Users/mujahidali/Documents/Codex/2026-09-30/a/work/MAnorm_targetTE_RNA_20261028/results/selected_TE_locus_UMI_by_mouse.tsv.gz`. Rows may repeat across the eight sets and must not be summed across sets.

LiSC jobs 7750731 (join audit) and 7750735 (locus measurement) both completed with exit code 0. The 70,470 per-set locus rows passed gzip integrity and the 64 plot rows passed four-mice-per-condition, balanced-sex checks.
