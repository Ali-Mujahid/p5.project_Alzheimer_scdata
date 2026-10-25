# Microglia gene differential expression — PyDESeq2 0.5.0

## Input and model

The analysis uses the raw integer gene UMI pseudobulk from 22,251 provisionally selected Microglia cells. Counts were summed separately for each of 20 mice, with four mice per group and two female and two male mice in every group. The source matrix has 55,487 feature IDs. Genes were filtered without using group labels: at least 10 raw UMIs in at least four mice. Each of WT_6mo, WT_21mo, 5xFAD_3mo, and APOE4_TREM2_3mo was contrasted against WT_3mo. PyDESeq2 v0.5.0 fitted `~ condition + sex`, with mouse as the replicate. Its median-of-ratios size factors, dispersion estimates and Wald tests produced the result tables. Benjamini–Hochberg adjusted p values were calculated within each contrast. FDR 0.05 is the primary list; FDR 0.10 is exploratory.

The per-contrast `all_genes` table retains every input gene and indicates whether it passed the common prefilter. Columns `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, and `padj` are PyDESeq2 outputs for eligible genes; excluded genes have missing model statistics. Positive log2 fold change means higher in the target group. `DEG_FDR005` and `DEG_FDR010` tables are subsets of the same model output, not separate model fits.

Volcano plots show Wald p values on the vertical axis; colors indicate adjusted p < 0.1. Heatmaps use the up to 60 lowest-adjusted-p genes at FDR < 0.1 per contrast. Each heatmap shows the eight mice in the paired comparison and row-wise z scores of log2(size-factor-normalized UMI + 1). Heatmap colors are `#3288bd` for low and `#d53e4f` for high. A blank significance set is reported as such and is not replaced with a nominal-hit heatmap.

## Distinct TE analysis

The IRescue Microglia TE-subfamily matrix contains fractional expected UMI allocations for multimapped reads. Those values were **not rounded or supplied to PyDESeq2**, which requires integer counts. The previously reviewed edgeR TE-subfamily analysis remains the TE-expression result and is shown separately in the atlas. Gene DEGs and TE associations require additional independent evidence; proximity or correlated mouse-level patterns alone do not prove regulation of a specific insertion.

## Interpretation

The selected Microglia population and its finer cluster labels remain provisional. Four mice per group limits power and increases sensitivity to an individual animal. The sample PCA has conspicuous mouse-level separation, including WT_21mo_female_1 and several 5xFAD mice; raw gene-UMI totals and size factors also vary markedly among mice. These are reported in the QC files and warrant cautious interpretation of single-gene disease findings. The model includes sex but does not interpret cell-level counts as independent animals. Gene expression and chromatin accessibility were measured in separate nuclei. Differential expression is an association with the group comparison, not a causal effect or proof of TE-copy activity.

## Reproducibility

The atlas provides the mouse QC table, full per-contrast gene tables, FDR lists, source hashes and model settings. The analysis source and wheel hashes are retained in the working project under `work/TE_RNA_PyDESeq2_20261026/`. Model job 7667741 wrote all four contrast results and `model_complete.json`, then exited with a plotting error because the 5xFAD contrast had only one FDR 0.1 gene. A separate plotting-only job, 7667756, completed successfully after disabling row clustering for that one-row heatmap. The model was not rerun. Checksums of all 29 final files are in the saved `complete.json` on LiSC under `Microglia_gene_PyDESeq2_20261026/job-7667741`.
